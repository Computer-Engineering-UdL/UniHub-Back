import uuid

from pydantic import BaseModel

from app.literals.users import Role


class TokenData(BaseModel):
    id: uuid.UUID
    username: str
    email: str
    role: Role = Role.BASIC
