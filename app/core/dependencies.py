from __future__ import annotations

import uuid

import redis
from authlib.integrations.starlette_client import OAuth
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import ValidationError
from starlette.requests import Request

from app.literals.auth import OAuthProvider
from app.literals.users import ROLE_HIERARCHY, Role

from .config import settings
from .types import TokenData

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_VERSION}/auth/login")
oauth = OAuth()

oauth.register(
    name=OAuthProvider.GOOGLE.value,
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

oauth.register(
    name=OAuthProvider.GITHUB.value,
    client_id=settings.GITHUB_CLIENT_ID,
    client_secret=settings.GITHUB_CLIENT_SECRET,
    access_token_url="https://github.com/login/oauth/access_token",
    authorize_url="https://github.com/login/oauth/authorize",
    api_base_url="https://api.github.com/",
    client_kwargs={"scope": "user:email"},
)


def get_oauth() -> OAuth:
    return oauth


def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
    """Validate JWT token and return current user"""

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: uuid.UUID = uuid.UUID(payload.get("sub"))
        username: str = payload.get("username")
        email: str = payload.get("email")
        role: Role = payload.get("role")

        token_data = TokenData(id=user_id, username=username, email=email, role=role)
    except (JWTError, ValidationError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

    return token_data


def require_role(min_role: Role):
    """Verify that the user has the required roles

    Args:
        min_role: Minimum role required to access
    Raises:
        HTTPException: If user does not have required roles
    """

    def role_checker(user: TokenData = Depends(get_current_user)) -> TokenData:
        if ROLE_HIERARCHY[user.role] > ROLE_HIERARCHY[min_role]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Requires elevated access")
        return user

    return role_checker


async def get_redis(request: Request) -> redis.Redis:
    return request.app.state.redis
