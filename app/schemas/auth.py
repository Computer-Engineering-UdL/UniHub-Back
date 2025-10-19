from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, field_validator

from app.literals.auth import TokenType

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


class AuthResponse(BaseModel):
    token: str
    user: UserRead


__all__ = [
    "LoginRequest",
    "Token",
    "AuthResponse",
]
