from __future__ import annotations

import asyncio
import uuid
from functools import wraps
from typing import Callable, Optional

from authlib.integrations.starlette_client import OAuth
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import ValidationError
from starlette.requests import Request

from app.literals.auth import OAuthProvider
from app.literals.users import ROLE_HIERARCHY, Role

from .config import settings
from .rate_limiter import CooldownManager, RateLimiter, RateLimitStrategy
from .types import TokenData

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_VERSION}/auth/login")

oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl=f"{settings.API_VERSION}/auth/login", auto_error=False)

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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    return token_data


def get_optional_current_user(token: str | None = Depends(oauth2_scheme_optional)) -> TokenData | None:
    """
    Validate JWT token if present, but return None if no token
    or if token is invalid. Allows anonymous access.
    """
    if token is None:
        return None

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: uuid.UUID = uuid.UUID(payload.get("sub"))
        username: str = payload.get("username")
        email: str = payload.get("email")
        role: Role = payload.get("role")
        token_data = TokenData(id=user_id, username=username, email=email, role=role)
    except (JWTError, ValidationError, ValueError):
        return None
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


def rate_limit(
    max_requests: int = 10,
    window_seconds: int = 60,
    strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW,
    key_prefix: str = "endpoint",
    per_user: bool = True,
):
    """
    Rate limit decorator for FastAPI endpoints

    Args:
        max_requests: Maximum requests allowed
        window_seconds: Time window in seconds
        strategy: Rate limiting strategy
        key_prefix: Prefix for the rate limit key
        per_user: If True, rate limit per user. If False, global rate limit
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user") or kwargs.get("user")
            request = kwargs.get("request")

            if per_user and current_user:
                key = f"{key_prefix}:{current_user.id}"
            elif request:
                client_ip = request.client.host
                key = f"{key_prefix}:{client_ip}"
            else:
                key = key_prefix

            is_allowed, remaining, retry_after = await RateLimiter.check_rate_limit(
                key=key, max_requests=max_requests, window_seconds=window_seconds, strategy=strategy
            )

            if not is_allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": "Rate limit exceeded",
                        "retry_after": retry_after,
                        "message": f"Too many requests. Please try again in {retry_after} seconds.",
                    },
                    headers={
                        "Retry-After": str(retry_after),
                        "X-RateLimit-Limit": str(max_requests),
                        "X-RateLimit-Remaining": str(remaining),
                        "X-RateLimit-Reset": str(retry_after),
                    },
                )

            result = func(*args, **kwargs)
            if asyncio.iscoroutine(result):
                return await result
            return result

        return wrapper

    return decorator


def cooldown(action: str, cooldown_seconds: int):
    """
    Cooldown decorator for specific actions
    Simpler than rate limiting - just enforces a wait between actions

    Args:
        action: Name of the action
        cooldown_seconds: Cooldown duration in seconds
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user") or kwargs.get("user")

            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required for this action"
                )

            can_perform, seconds_remaining = await CooldownManager.check_cooldown(
                user_id=current_user.id, action=action, cooldown_seconds=cooldown_seconds
            )

            if not can_perform:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": "Action on cooldown",
                        "action": action,
                        "retry_after": seconds_remaining,
                        "message": f"Please wait {seconds_remaining} seconds before performing this action again.",
                    },
                    headers={"Retry-After": str(seconds_remaining)},
                )
            result = func(*args, **kwargs)
            if asyncio.iscoroutine(result):
                return await result
            return result

        return wrapper

    return decorator


async def check_rate_limit_dependency(
    request: Request,
    current_user: Optional[TokenData] = Depends(get_current_user),
    max_requests: int = 10,
    window_seconds: int = 60,
):
    """
    Dependency function for rate limiting
    """
    if current_user:
        key = f"api:{request.url.path}:{current_user.id}"
    else:
        key = f"api:{request.url.path}:{request.client.host}"

    is_allowed, remaining, retry_after = await RateLimiter.check_rate_limit(
        key=key, max_requests=max_requests, window_seconds=window_seconds
    )

    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Retry after {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)},
        )
