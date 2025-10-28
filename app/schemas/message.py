import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas import ChannelRead, UserRead


class MessageBase(BaseModel):
    content: str = Field(min_length=1, max_length=500)
    channel_id: uuid.UUID
    user_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


class MessageCreate(MessageBase):
    pass


class MessageUpdate(BaseModel):
    content: str = Field(min_length=1, max_length=500)

    model_config = ConfigDict(from_attributes=True)


class MessageAnswer(MessageBase):
    parent_message_id: uuid.UUID = None

    model_config = ConfigDict(from_attributes=True)


class MessageRead(MessageBase):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    is_edited: bool = Field(default=False)
    parent_message_id: Optional[uuid.UUID] = None

    model_config = ConfigDict(from_attributes=True)


class MessageDetail(MessageBase):
    user: UserRead
    channel: ChannelRead
    parent_message: Optional["MessageRead"] = None

    model_config = ConfigDict(from_attributes=True)


__all__ = [
    "MessageBase",
    "MessageCreate",
    "MessageUpdate",
    "MessageRead",
    "MessageDetail",
    "MessageAnswer",
]
