from pydantic import BaseModel, EmailStr

from app.models import UserPublic


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    token: str
    user: UserPublic
