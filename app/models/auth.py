from pydantic import BaseModel, EmailStr
from typing import Optional, Literal

Role = Literal["Basic", "Admin"]
Provider = Literal["local", "google", "github"]


class User(BaseModel):
    id: str
    email: EmailStr
    name: str
    provider: Provider = "local"
    role: Role = "Basic"
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    phone: Optional[str] = None
    university: Optional[str] = None


class UserInDB(User):
    hashed_password: str


class UserPublic(BaseModel):
    id: str
    email: EmailStr
    name: str
    provider: Provider
    role: Role


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    token: str
    user: UserPublic
