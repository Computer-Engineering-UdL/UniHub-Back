import datetime
import uuid
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Message
from app.repositories.base import BaseRepository


class MessageRepository(BaseRepository[Message]):
    """Repository for Message entity."""

    def __init__(self, db: Session):
        super().__init__(Message, db)
        self.model = self.model_class

    def create(self, message_data: dict) -> Message:
        """Create a new message."""
        message = Message(**message_data)
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def get_channel_messages(self, channel_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[Message]:
        """Get all messages from a channel with pagination."""
        stmt = select(Message).filter(Message.channel_id == channel_id).offset(skip).limit(limit)
        return list(self.db.scalars(stmt).all())

    def get_user_messages(self, user_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[Message]:
        """Get all messages from a user with pagination."""
        stmt = select(Message).filter(Message.user_id == user_id).offset(skip).limit(limit)
        return list(self.db.scalars(stmt).all())

    def update(self, message_id: uuid.UUID, update_data: dict) -> Optional[Message]:
        """Update a message."""
        message = self.get_by_id(message_id)
        if not message:
            return None

        for key, value in update_data.items():
            if hasattr(message, key):
                setattr(message, key, value)

        message.is_edited = True
        message.updated_at = datetime.datetime.now(datetime.UTC)

        self.db.commit()
        self.db.refresh(message)
        return message

    def create_reply(self, parent_message_id: uuid.UUID, message_data: dict) -> Optional[Message]:
        """Create a reply to an existing message."""
        parent = self.get_by_id(parent_message_id)
        if not parent:
            return None

        message_data["parent_message_id"] = parent_message_id
        return self.create(message_data)
