from __future__ import annotations

import datetime
import uuid
from datetime import timedelta
from typing import TYPE_CHECKING, Any, Dict, Optional

import bcrypt
from jose import jwt

from app.core.config import settings

if TYPE_CHECKING:
    from app.models import User


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(data: dict, expire_minutes: Optional[int] = None):
    to_encode = data.copy()
    expire = datetime.datetime.now(datetime.UTC) + timedelta(
        minutes=expire_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire, "type": "access", "jti": str(uuid.uuid4())})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_payload_from_user(db_user: User) -> Dict[str, Any]:
    return {"sub": str(db_user.id), "username": db_user.username, "email": db_user.email, "role": db_user.role}


def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.datetime.now(datetime.UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh", "jti": str(uuid.uuid4())})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
