from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from pydantic import BaseModel, field_validator

from app.literals.auth import TokenType
from app.literals.users import Role

if TYPE_CHECKING:
    from app.schemas import UserRead


class LoginRequest(BaseModel):
    username: str
    password: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        if not v or not v.strip():
            raise ValueError("Username/email cannot be empty")
        return v.strip()


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: TokenType = "bearer"


class TokenData(BaseModel):
    id: uuid.UUID
    username: str
    email: str
    role: Role = Role.BASIC


class AuthResponse(BaseModel):
    token: str
    user: UserRead


__all__ = [
    "LoginRequest",
    "Token",
    "TokenData",
    "AuthResponse",
]
