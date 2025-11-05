import uuid
from typing import Optional

from sqlalchemy import desc, func, or_
from sqlalchemy.orm import Session

from app.models import Conversation, ConversationMessage
from app.schemas import ConversationCreate, ConversationMessageCreate


class ConversationCRUD:
    """CRUD operations for private conversations."""

    @staticmethod
    def get_or_create_conversation(
        db: Session,
        user1_id: uuid.UUID,
        user2_id: uuid.UUID,
        housing_offer_id: Optional[uuid.UUID] = None,
    ) -> Conversation:
        """
        Get existing conversation or create new one.
        Always stores user IDs in sorted order to avoid duplicates.

        Returns: (conversation, created) where created is True if new conversation
        """

        sorted_ids = sorted([user1_id, user2_id], key=str)

        conversation = (
            db.query(Conversation)
            .filter(
                Conversation.user1_id == sorted_ids[0],
                Conversation.user2_id == sorted_ids[1],
                Conversation.housing_offer_id == housing_offer_id,
            )
            .first()
        )

        if conversation:
            return conversation

        conversation = Conversation(
            user1_id=sorted_ids[0],
            user2_id=sorted_ids[1],
            housing_offer_id=housing_offer_id,
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        return conversation

    @staticmethod
    def create_conversation(
        db: Session,
        user_id: uuid.UUID,
        conversation_in: ConversationCreate,
    ) -> Conversation:
        """
        Create a new conversation with optional initial message.
        """
        conversation = ConversationCRUD.get_or_create_conversation(
            db,
            user_id,
            conversation_in.other_user_id,
            conversation_in.housing_offer_id,
        )

        if conversation_in.initial_message:
            ConversationCRUD.send_message(
                db,
                conversation.id,
                user_id,
                ConversationMessageCreate(content=conversation_in.initial_message),
            )

        return conversation

    @staticmethod
    def get_user_conversations(
        db: Session,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Conversation]:
        """
        Get all conversations for a user, ordered by most recent message.
        """
        conversations = (
            db.query(Conversation)
            .filter(
                or_(
                    Conversation.user1_id == user_id,
                    Conversation.user2_id == user_id,
                )
            )
            .order_by(desc(Conversation.last_message_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
        return conversations

    @staticmethod
    def get_conversation_by_id(
        db: Session,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Optional[Conversation]:
        """
        Get a conversation by ID if user is a participant.
        """
        conversation = (
            db.query(Conversation)
            .filter(
                Conversation.id == conversation_id,
                or_(
                    Conversation.user1_id == user_id,
                    Conversation.user2_id == user_id,
                ),
            )
            .first()
        )
        return conversation

    @staticmethod
    def send_message(
        db: Session,
        conversation_id: uuid.UUID,
        sender_id: uuid.UUID,
        message_in: ConversationMessageCreate,
    ) -> ConversationMessage:
        """
        Send a message in a conversation.
        """
        message = ConversationMessage(
            conversation_id=conversation_id,
            sender_id=sender_id,
            content=message_in.content,
        )
        db.add(message)

        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if conversation:
            conversation.last_message_at = message.created_at

        db.commit()
        db.refresh(message)
        return message

    @staticmethod
    def get_conversation_messages(
        db: Session,
        conversation_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ConversationMessage]:
        """
        Get messages from a conversation.
        """
        messages = (
            db.query(ConversationMessage)
            .filter(ConversationMessage.conversation_id == conversation_id)
            .order_by(ConversationMessage.created_at)
            .offset(skip)
            .limit(limit)
            .all()
        )
        return messages

    @staticmethod
    def mark_messages_as_read(
        db: Session,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> int:
        """
        Mark all unread messages in a conversation as read for a user.
        Returns number of messages marked as read.
        """
        result = (
            db.query(ConversationMessage)
            .filter(
                ConversationMessage.conversation_id == conversation_id,
                ConversationMessage.sender_id != user_id,
                ConversationMessage.is_read.is_(False),
            )
            .update({"is_read": True})
        )
        db.commit()
        return result

    @staticmethod
    def get_unread_count(
        db: Session,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> int:
        """
        Get count of unread messages for a user in a conversation.
        """
        count = (
            db.query(func.count(ConversationMessage.id))
            .filter(
                ConversationMessage.conversation_id == conversation_id,
                ConversationMessage.sender_id != user_id,
                ConversationMessage.is_read.is_(False),
            )
            .scalar()
        )
        return count or 0

    @staticmethod
    def delete_conversation(
        db: Session,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> bool:
        """
        Delete a conversation if user is a participant.
        Returns True if deleted, False if not found or unauthorized.
        """
        conversation = (
            db.query(Conversation)
            .filter(
                Conversation.id == conversation_id,
                or_(
                    Conversation.user1_id == user_id,
                    Conversation.user2_id == user_id,
                ),
            )
            .first()
        )

        if not conversation:
            return False

        db.delete(conversation)
        db.commit()
        return True
