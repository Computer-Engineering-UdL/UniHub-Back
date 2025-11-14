import re
import uuid

from authlib.integrations.starlette_client import OAuth
from fastapi import HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from starlette.requests import Request

from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, verify_password
from app.domains import UserRepository
from app.literals.auth import OAuthProvider
from app.models import create_payload_from_user
from app.schemas import LoginRequest, Token


class AuthService:
    """Service layer for authentication-related business logic."""

    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)

    def authenticate_user(self, login_request: LoginRequest) -> Token:
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

        data = create_payload_from_user(user)
        access_token = create_access_token(data=data)
        refresh_token = create_refresh_token(data=data)

        return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")

    def refresh_token(self, refresh_token: str) -> Token:
        """Refresh access token using a valid refresh token."""
        payload = self._verify_token(refresh_token, expected_type="refresh")
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

        data = create_payload_from_user(user)
        access_token = create_access_token(data=data)
        refresh_token = create_refresh_token(data=data)

        return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")

    @staticmethod
    def _verify_token(token: str, expected_type: str = None) -> dict:
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

            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )


def verify_token(token: str, expected_type: str = None) -> dict:
    """Standalone function for token verification (for backwards compatibility)."""
    return AuthService._verify_token(token, expected_type)


__all__ = ["AuthService", "verify_token"]
