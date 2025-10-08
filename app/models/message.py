import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

import sqlalchemy as sa
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models import User


class Message(BaseModel):
    id: uuid.UUID = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str = Field(min_length=1, max_length=500)
    channel_id: str
    user_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    is_edited: bool = Field(default=False)
    parent_message_id: Optional[str] = None

    user: Optional["User"] = None

    model_config = ConfigDict(from_attributes=True)


class MessageTableModel(Base):
    __tablename__ = "message"

    id = Column(sa.UUID, primary_key=True, default=uuid.uuid4)
    content = Column(sa.String(500), nullable=False)
    channel_id = Column(sa.UUID, ForeignKey("channel.id"), nullable=False)
    user_id = Column(sa.UUID, ForeignKey("user.id"), nullable=False)
    created_at = Column(sa.DateTime, nullable=False, default=datetime.now)
    updated_at = Column(sa.DateTime, nullable=True)
    is_edited = Column(sa.Boolean, nullable=False, default=False)
    parent_message_id = Column(sa.UUID, ForeignKey("message.id"), nullable=True)

    user = relationship("UserTableModel", back_populates="messages")
    channel = relationship("ChannelTableModel", back_populates="messages")

    parent_message = relationship("MessageTableModel", remote_side=[id], backref="replies")
