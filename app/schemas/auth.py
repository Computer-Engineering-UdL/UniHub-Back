from pydantic import BaseModel, EmailStr

from app.schemas import UserPublic


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    token: str
    user: UserPublic
