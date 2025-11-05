import datetime
import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ConversationMessageCreate(BaseModel):
    """Schema for creating a new message in a conversation."""

    content: str = Field(min_length=1, max_length=2000)


class ConversationMessageRead(BaseModel):
    """Schema for reading a conversation message."""

    id: uuid.UUID
    conversation_id: uuid.UUID
    sender_id: uuid.UUID
    content: str
    created_at: datetime.datetime
    is_read: bool

    model_config = ConfigDict(from_attributes=True)


class ConversationCreate(BaseModel):
    """Schema for creating a new conversation."""

    other_user_id: uuid.UUID
    housing_offer_id: Optional[uuid.UUID] = None
    initial_message: Optional[str] = Field(None, min_length=1, max_length=2000)


class ConversationRead(BaseModel):
    """Schema for reading a conversation (list view)."""

    id: uuid.UUID
    user1_id: uuid.UUID
    user2_id: uuid.UUID
    housing_offer_id: Optional[uuid.UUID]
    created_at: datetime.datetime
    last_message_at: Optional[datetime.datetime]
    unread_count: int = 0
    last_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ConversationDetail(ConversationRead):
    """Schema for reading a conversation with all messages."""

    messages: list[ConversationMessageRead] = []

    model_config = ConfigDict(from_attributes=True)


__all__ = [
    "ConversationMessageCreate",
    "ConversationMessageRead",
    "ConversationCreate",
    "ConversationRead",
    "ConversationDetail",
]
