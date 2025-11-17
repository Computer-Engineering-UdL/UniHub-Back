from __future__ import annotations

import datetime
import uuid
from typing import TYPE_CHECKING, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.security import hash_password
from app.literals.users import Role
from app.schemas.university import FacultyRead

if TYPE_CHECKING:
    from .interest import InterestRead

Provider = Literal["local", "google", "github"]


# ==========================================
# User Base Schema
# ==========================================
class UserBase(BaseModel):
    """Base schema with common user fields."""

    username: str = Field(min_length=1, max_length=50)
    email: EmailStr
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    faculty_id: Optional[uuid.UUID] = None
    year_of_study: Optional[int] = Field(None, ge=1, le=12)
    avatar_url: Optional[str] = Field(None, max_length=500)
    room_number: Optional[str] = Field(None, max_length=20)
    is_active: bool = Field(default=True)
    is_verified: bool = Field(default=False)
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)


# ==========================================
# Create Schema (for POST)
# ==========================================
class UserCreate(UserBase):
    """Schema for creating a new user via POST."""

    password: str = Field(min_length=8, max_length=255)
    provider: Provider = Field(default="local")
    role: Role = Field(default=Role.BASIC)

    @field_validator("password")
    @classmethod
    def hash_password(cls, value: str) -> str:
        """Hash password."""
        return hash_password(value)

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# Update Schema (for PATCH)
# ==========================================
class UserUpdate(BaseModel):
    """Schema for updating a user via PATCH."""

    username: Optional[str] = Field(None, min_length=1, max_length=50)
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    faculty: Optional[FacultyRead] = None
    year_of_study: Optional[int] = Field(None, ge=1, le=12)
    avatar_url: Optional[str] = Field(None, max_length=500)
    is_verified: Optional[bool] = None
    role: Optional[Role] = None

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# Read Schema (for GET responses)
# ==========================================
class UserRead(UserBase):
    """Basic user info for GET responses."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    provider: Provider
    role: Role
    is_active: bool
    is_verified: bool
    created_at: datetime.datetime
    model_config = ConfigDict(from_attributes=True)


# ==========================================
# List Schema (for paginated list endpoints)
# ==========================================
class UserList(BaseModel):
    """Lightweight schema for list endpoints."""

    id: uuid.UUID
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    role: Role
    is_verified: bool
    created_at: datetime.datetime
    model_config = ConfigDict(from_attributes=True)


class UserSimplified(BaseModel):
    """Lightweight schema for list endpoints."""

    id: uuid.UUID
    username: str
    model_config = ConfigDict(from_attributes=True)


# ==========================================
# Public Schema (for external APIs)
# ==========================================
class UserPublic(BaseModel):
    id: uuid.UUID
    username: str
    first_name: str
    last_name: str
    avatar_url: Optional[str] = Field(None, max_length=500)
    faculty: Optional[FacultyRead] = None
    is_verified: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# Sensitive Operations Schemas
# ==========================================
class UserPasswordChange(BaseModel):
    """Schema for password change endpoint."""

    current_password: str = Field(min_length=8)
    new_password: str = Field(min_length=8, max_length=255)
    confirm_password: str = Field(min_length=8)


class RoleUpdate(BaseModel):
    """Schema for role updates."""

    role: Role


class UserVerify(BaseModel):
    """Schema for email verification."""

    verification_token: str


# ==========================================
# Detail Schema (with relationships)
# ==========================================
class UserDetail(UserRead):
    """
    Full user profile.
    """

    interests: List[InterestRead]
    housing_offer_count: int = 0
    housing_search_count: int = 0
    listings_active: int = 0

# ==========================================
# Register Schema (for sign-up endpoint)
# ==========================================
class UserRegister(BaseModel):
    """Schema used for public user registration."""

    username: str = Field(min_length=1, max_length=50)
    email: EmailStr
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8, max_length=255)

    model_config = ConfigDict(from_attributes=True)


__all__ = [
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserRead",
    "UserList",
    "UserPasswordChange",
    "RoleUpdate",
    "UserVerify",
    "UserDetail",
    "UserPublic",
    "UserSimplified",
    "UserRegister"
]
