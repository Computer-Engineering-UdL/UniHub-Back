import uuid
from typing import TYPE_CHECKING

from pydantic import BaseModel

from app.literals.users import Role

if TYPE_CHECKING:
    from app.schemas import UserPublic


class LoginRequest(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    id: uuid.UUID
    username: str
    email: str
    role: Role = "Basic"


class AuthResponse(BaseModel):
    token: str
    user: "UserPublic"
