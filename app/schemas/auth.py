from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from pydantic import BaseModel

from app.literals.auth import TokenType
from app.literals.users import Role

if TYPE_CHECKING:
    from app.schemas import UserRead


class LoginRequest(BaseModel):
    username: str
    password: str


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
