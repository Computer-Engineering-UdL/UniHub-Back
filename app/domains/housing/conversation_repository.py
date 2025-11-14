import uuid
from typing import List, Optional

from sqlalchemy import desc, func, or_, select
from sqlalchemy.orm import Session

from app.models import Conversation, ConversationMessage
from app.repositories.base import BaseRepository


class ConversationRepository(BaseRepository[Conversation]):
    """Repository for Conversation and ConversationMessage entities."""

    def __init__(self, db: Session):
        super().__init__(Conversation, db)
        self.model = self.model_class

    def get_or_create_conversation(
        self,
        user1_id: uuid.UUID,
        user2_id: uuid.UUID,
        housing_offer_id: Optional[uuid.UUID] = None,
    ) -> Conversation:
        """Get existing conversation or create new one."""
        sorted_ids = sorted([user1_id, user2_id], key=str)

        stmt = select(Conversation).filter(
            Conversation.user1_id == sorted_ids[0],
            Conversation.user2_id == sorted_ids[1],
            Conversation.housing_offer_id == housing_offer_id,
        )
        conversation = self.db.scalar(stmt)

        if conversation:
            return conversation

        conversation = Conversation(
            user1_id=sorted_ids[0],
            user2_id=sorted_ids[1],
            housing_offer_id=housing_offer_id,
        )
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def get_by_id(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID = None,
    ) -> Optional[Conversation]:
        """Get conversation by ID, optionally filtering by user participation."""
        stmt = select(Conversation).filter(Conversation.id == conversation_id)

        if user_id is not None:
            stmt = stmt.filter(
                or_(
                    Conversation.user1_id == user_id,
                    Conversation.user2_id == user_id,
                )
            )

        return self.db.scalar(stmt)

    def get_by_id_for_user(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Optional[Conversation]:
        """Get conversation by ID if user is a participant."""
        return self.get_by_id(conversation_id, user_id)

    def get_user_conversations(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Conversation]:
        """Get all conversations for a user."""
        stmt = (
            select(Conversation)
            .filter(
                or_(
                    Conversation.user1_id == user_id,
                    Conversation.user2_id == user_id,
                )
            )
            .order_by(desc(Conversation.last_message_at))
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def send_message(
        self,
        conversation_id: uuid.UUID,
        sender_id: uuid.UUID,
        content: str,
    ) -> ConversationMessage:
        """Send a message in a conversation."""
        message = ConversationMessage(
            conversation_id=conversation_id,
            sender_id=sender_id,
            content=content,
        )
        self.db.add(message)

        stmt = select(Conversation).filter(Conversation.id == conversation_id)
        conversation = self.db.scalar(stmt)
        if conversation:
            conversation.last_message_at = message.created_at

        self.db.commit()
        self.db.refresh(message)
        return message

    def get_messages(
        self,
        conversation_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ConversationMessage]:
        """Get messages from a conversation."""
        stmt = (
            select(ConversationMessage)
            .filter(ConversationMessage.conversation_id == conversation_id)
            .order_by(ConversationMessage.created_at)
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def mark_messages_as_read(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> int:
        """Mark all unread messages in a conversation as read."""
        stmt = select(ConversationMessage).filter(
            ConversationMessage.conversation_id == conversation_id,
            ConversationMessage.sender_id != user_id,
            ConversationMessage.is_read.is_(False),
        )
        messages = list(self.db.scalars(stmt).all())
        count = len(messages)
        for message in messages:
            message.is_read = True
        self.db.commit()
        return count

    def get_unread_count(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> int:
        """Get count of unread messages."""
        stmt = select(func.count(ConversationMessage.id)).filter(
            ConversationMessage.conversation_id == conversation_id,
            ConversationMessage.sender_id != user_id,
            ConversationMessage.is_read.is_(False),
        )
        count = self.db.scalar(stmt)
        return count or 0
