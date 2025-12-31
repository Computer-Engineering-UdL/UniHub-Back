import datetime
import re
import secrets
import uuid
from typing import Optional

from authlib.integrations.starlette_client import OAuth
from fastapi import HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from starlette.requests import Request

from app.core.config import settings
from app.core.email_service import email_service
from app.core.security import create_access_token, create_refresh_token, hash_password, verify_password
from app.core.valkey import valkey_client
from app.domains import UserRepository
from app.domains.auth.password_validator import PasswordValidator
from app.literals.auth import OAuthProvider
from app.models import create_payload_from_user
from app.schemas import LoginRequest, Token


class AuthService:
    """Service layer for authentication-related business logic."""

    VERIFICATION_TOKEN_PREFIX = "verify_email:"
    PASSWORD_RESET_TOKEN_PREFIX = "password_reset:"

    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)
        self.password_validator = PasswordValidator(db)

    async def authenticate_user(self, login_request: LoginRequest) -> Token:
        """Authenticate a user and return tokens."""
        email_pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"

        if re.match(email_pattern, login_request.username):
            user = self.user_repository.get_by_email(login_request.username)
        else:
            user = self.user_repository.get_by_username(login_request.username)

        if not user or not verify_password(login_request.password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive",
            )

        if user.is_banned:
            detail = {
                "message": "User account is banned",
                "banned_until": user.banned_until.isoformat() if user.banned_until else None,
            }

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=detail,
            )

        data = create_payload_from_user(user)
        access_token = create_access_token(data=data)
        refresh_token = create_refresh_token(data=data)
        token = Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")
        token_store = await valkey_client.get(str(user.id))
        if token_store is None:
            token_store = list()
        token_store.append(token)
        await valkey_client.set(str(user.id), token_store)
        return token

    async def invalidate_tokens(self, token: str) -> bool:
        """Invalidate all tokens for a given user"""
        token_payload = await self._verify_token(token)
        user_id: str = token_payload["sub"]
        if not await valkey_client.has(user_id):
            return False
        await valkey_client.unset(user_id)
        return True

    async def invalidate_token(self, token: str) -> bool:
        """Invalidate the given token and its refresh for a user"""
        token_payload = await self._verify_token(token)
        user_id: str = token_payload["sub"]
        token_store: Optional[list] = await valkey_client.get(user_id)
        if not token_store:
            return False
        try:
            token_store = [v for v in token_store if v["access_token"] != token]
        except ValueError:
            return False
        if not len(token_store):
            await valkey_client.unset(user_id)
        else:
            await valkey_client.set(user_id, token_store)
        return True

    async def refresh_token(self, refresh_token: str) -> Token:
        """Refresh access token using a valid refresh token."""
        payload = await self._verify_token(refresh_token, expected_type="refresh")
        user = self.user_repository.get_by_id(uuid.UUID(payload.get("sub")))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )

        data = create_payload_from_user(user)
        access_token = create_access_token(data=data)
        new_refresh_token = create_refresh_token(data=data)

        return Token(access_token=access_token, refresh_token=new_refresh_token, token_type="bearer")

    async def send_verification_email(self, email: str) -> bool:
        """
        Send a verification email to the user.
        """
        user = self.user_repository.get_by_email(email)

        if not user:
            return True

        if user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is already verified",
            )

        token = secrets.token_urlsafe(32)

        key = f"{self.VERIFICATION_TOKEN_PREFIX}{token}"
        await valkey_client.client.setex(
            key,
            settings.VERIFICATION_TOKEN_EXPIRE_HOURS * 3600,
            str(user.id),
        )

        email_service.send_verification_email(
            to_email=user.email,
            token=token,
            username=user.username,
        )

        return True

    async def confirm_email_verification(self, token: str) -> bool:
        """Confirm email verification using the token."""
        key = f"{self.VERIFICATION_TOKEN_PREFIX}{token}"
        user_id_str = await valkey_client.client.get(key)

        if not user_id_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token",
            )

        if isinstance(user_id_str, bytes):
            user_id_str = user_id_str.decode("utf-8")

        user = self.user_repository.get_by_id(uuid.UUID(user_id_str))

        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User not found",
            )

        if user.is_verified:
            await valkey_client.client.delete(key)
            return True

        user.is_verified = True
        user.verified_at = datetime.datetime.now(datetime.UTC)
        self.db.commit()

        await valkey_client.client.delete(key)

        return True

    async def send_password_reset(self, email: str, client_ip: str) -> bool:
        """
        Send a password reset email.
        """
        user = self.user_repository.get_by_email(email)

        if not user:
            return True

        if not user.is_active:
            return True

        token = secrets.token_urlsafe(32)

        key = f"{self.PASSWORD_RESET_TOKEN_PREFIX}{token}"
        await valkey_client.client.setex(
            key,
            settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS * 3600,
            str(user.id),
        )

        email_service.send_password_reset_email(
            to_email=user.email,
            token=token,
            username=user.username,
        )

        return True

    async def reset_password(self, token: str, new_password: str) -> bool:
        """Reset password using a valid reset token."""
        key = f"{self.PASSWORD_RESET_TOKEN_PREFIX}{token}"
        user_id_str = await valkey_client.client.get(key)

        if not user_id_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired password reset token",
            )

        if isinstance(user_id_str, bytes):
            user_id_str = user_id_str.decode("utf-8")

        user_id = uuid.UUID(user_id_str)
        user = self.user_repository.get_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User not found",
            )

        self.password_validator.validate_and_check_history(user_id, new_password)

        hashed = hash_password(new_password)

        self.password_validator.add_to_history(user_id, user.password)

        user.password = hashed
        self.db.commit()

        await valkey_client.client.delete(key)

        await valkey_client.unset(str(user_id))

        return True

    async def change_password(self, user_id: uuid.UUID, current_password: str, new_password: str) -> bool:
        """
        Change password for an authenticated user.
        """
        user = self.user_repository.get_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        if not verify_password(current_password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Current password is incorrect",
            )

        self.password_validator.validate_and_check_history(user_id, new_password)

        hashed = hash_password(new_password)

        self.password_validator.add_to_history(user_id, user.password)

        user.password = hashed
        self.db.commit()

        return True

    async def oauth_callback(
        self,
        provider: OAuthProvider,
        request: Request,
        oauth: OAuth,
    ) -> Token:
        """Handle OAuth callback and authenticate user."""
        provider_str = provider.value
        oauth_client = oauth.create_client(provider_str)
        token = await oauth_client.authorize_access_token(request)

        if provider == OAuthProvider.GOOGLE:
            user_info = token.get("userinfo")
            if not user_info:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials",
                )
            email = user_info["email"]
        elif provider == OAuthProvider.GITHUB:
            email_resp = await oauth_client.get("user/emails", token=token)
            email = next(e["email"] for e in email_resp.json() if e["primary"])
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported OAuth provider",
            )

        user = self.user_repository.get_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found. Please register first.",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive",
            )

        if user.is_banned:
            detail = {
                "message": "User account is banned",
                "banned_until": user.banned_until.isoformat() if user.banned_until else None,
            }

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=detail,
            )

        data = create_payload_from_user(user)
        access_token = create_access_token(data=data)
        refresh_token = create_refresh_token(data=data)

        return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")

    @staticmethod
    async def _verify_token(token: str, expected_type: str = None) -> dict:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id = payload.get("sub")
            username = payload.get("username")
            email = payload.get("email")
            role = payload.get("role")
            token_type = payload.get("type")

            if user_id is None or username is None or email is None or role is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired token",
                )

            if expected_type and token_type != expected_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Expected {expected_type} token",
                )

            if token_type == "refresh":
                auth_info: list[Token] = await valkey_client.get(user_id)
                refresh_token = next(auth["refresh_token"] for auth in auth_info if auth["refresh_token"] == token)
                if not auth_info or refresh_token != token:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid or expired refresh token",
                    )

            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )


async def verify_token(token: str, expected_type: str = None) -> dict:
    """Standalone function for token verification (for backwards compatibility)."""
    return await AuthService._verify_token(token, expected_type)


__all__ = ["AuthService", "verify_token"]
