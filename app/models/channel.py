import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Literal, Optional

import sqlalchemy as sa
from pydantic import BaseModel, ConfigDict, Field, HttpUrl
from sqlalchemy import Column, ForeignKey, Table
from sqlalchemy.orm import relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User

ChannelType = Literal["public", "private", "announcement"]

channel_members = Table(
    "channel_members",
    Base.metadata,
    Column("channel_id", sa.UUID, ForeignKey("channel.id"), primary_key=True),
    Column("user_id", sa.UUID, ForeignKey("user.id"), primary_key=True),
)

channel_messages = Table(
    "channel_messages",
    Base.metadata,
    Column("channel_id", sa.UUID, ForeignKey("channel.id"), primary_key=True),
    Column("message_id", sa.UUID, ForeignKey("message.id"), primary_key=True),
)


class Channel(BaseModel):
    id: uuid.UUID = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(min_length=1, max_length=60)
    description: Optional[str] = Field(None, max_length=120)
    channel_type: ChannelType = Field(default="public")
    created_at: datetime = Field(default_factory=datetime.now)
    channel_logo: Optional[HttpUrl] = None
    members: List["User"] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ChannelTableModel(Base):
    __tablename__ = "channel"

    id = Column(sa.UUID, primary_key=True, default=uuid.uuid4)
    name = Column(sa.String(60), nullable=False)
    description = Column(sa.String(120), nullable=True)
    channel_type = Column(sa.String(50), nullable=False, default="public")
    created_at = Column(sa.DateTime, nullable=False, default=datetime.now)
    channel_logo = Column(sa.String(255), nullable=True)

    members = relationship("UserTableModel", secondary=channel_members, back_populates="channels")
    messages = relationship("MessageTableModel", back_populates="channel", cascade="all, delete-orphan")
