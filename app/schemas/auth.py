from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, EmailStr, Field, field_validator

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


class VerificationSendRequest(BaseModel):
    """Request to send a verification email."""

    email: EmailStr

    @field_validator("email")
    @classmethod
    def email_to_lower(cls, v: str) -> str:
        return v.lower()


class VerificationConfirmRequest(BaseModel):
    """Request to confirm email verification."""

    token: str = Field(..., min_length=1)


# Password Reset Schemas
class PasswordForgotRequest(BaseModel):
    """Request to initiate password reset."""

    email: EmailStr

    @field_validator("email")
    @classmethod
    def email_to_lower(cls, v: str) -> str:
        return v.lower()


class PasswordResetRequest(BaseModel):
    """Request to reset password with token."""

    token: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=255)
    confirm_password: str = Field(..., min_length=8)

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v, info):
        if "new_password" in info.data and v != info.data["new_password"]:
            raise ValueError("Passwords do not match")
        return v


class PasswordChangeRequest(BaseModel):
    """Request to change password (authenticated user)."""

    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=255)
    confirm_password: str = Field(..., min_length=8)

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v, info):
        if "new_password" in info.data and v != info.data["new_password"]:
            raise ValueError("Passwords do not match")
        return v


# Generic Response
class MessageResponse(BaseModel):
    """Generic message response."""

    message: str


class OAuthUserInfo(BaseModel):
    """Internal schema for passing OAuth user info."""

    email: EmailStr
    first_name: str | None = None
    last_name: str | None = None
    avatar_url: str | None = None


__all__ = [
    "LoginRequest",
    "Token",
    "AuthResponse",
    "VerificationSendRequest",
    "VerificationConfirmRequest",
    "PasswordForgotRequest",
    "PasswordResetRequest",
    "PasswordChangeRequest",
    "MessageResponse",
    "OAuthUserInfo",
]
