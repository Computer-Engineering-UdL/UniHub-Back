import uuid
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.literals.users import Role

Provider = Literal["local", "google", "github"]


class User(BaseModel):
    id: UUID = Field(default_factory=uuid.uuid4)
    username: str = Field(min_length=1, max_length=20)
    email: EmailStr
    first_name: str = Field(min_length=1, max_length=30)
    last_name: str = Field(min_length=1, max_length=30)
    provider: Provider = Field(default="local")
    role: Role = Field(default="Basic")
    phone: Optional[str] = Field(default=None)
    university: Optional[str] = Field(default=None)

    model_config = ConfigDict(from_attributes=True)


class UserInDB(User):
    hashed_password: str


class UserPublic(BaseModel):
    id: UUID
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    provider: Provider
    role: Role
    phone: Optional[str] = None
    university: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
