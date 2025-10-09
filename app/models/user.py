import uuid
from typing import Literal, Optional
from uuid import UUID

import sqlalchemy as sa
from pydantic import BaseModel, ConfigDict, EmailStr, HttpUrl, Field
from sqlalchemy import Column
from sqlalchemy.orm import relationship

from app.core.database import Base

Role = Literal["Basic", "Admin"]
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
    avatar_url: Optional[HttpUrl] = None
    phone: Optional[str] = None
    university: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class UserTableModel(Base):
    __tablename__ = "user"

    id = Column(sa.UUID, primary_key=True, default=uuid.uuid4)
    username = Column(sa.String(20), unique=True, nullable=False, index=True)
    email = Column(sa.String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(sa.String(255), nullable=False)
    first_name = Column(sa.String(30), nullable=False)
    last_name = Column(sa.String(30), nullable=False)
    provider = Column(sa.String(50), nullable=False, default="local")
    role = Column(sa.String(25), nullable=False, default="Basic")
    avatar_url = Column(sa.String(255), nullable=True)
    phone = Column(sa.String(25), nullable=True)
    university = Column(sa.String(125), nullable=True)

    channels = relationship("ChannelTableModel", secondary="channel_members", back_populates="members")
    messages = relationship("MessageTableModel", back_populates="user")
    housing_offers = relationship("HousingOfferTableModel", back_populates="user")
