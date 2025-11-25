import uuid
from typing import List

from fastapi import HTTPException
from sqlalchemy.orm import Session
from starlette import status

from app.domains.housing.conversation_repository import ConversationRepository
from app.domains.websocket.websocket_service import ws_service
from app.schemas import (
    ConversationCreate,
    ConversationDetail,
    ConversationMessageCreate,
    ConversationMessageRead,
    ConversationRead,
)


class ConversationService:
    """Service layer for conversation business logic."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = ConversationRepository(db)

    def create_conversation(
        self,
        user_id: uuid.UUID,
        conversation_in: ConversationCreate,
    ) -> ConversationRead:
        """Create a new conversation with optional initial message."""
        if conversation_in.other_user_id == user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot create conversation with yourself",
            )

        conversation = self.repository.get_or_create_conversation(
            user_id,
            conversation_in.other_user_id,
            conversation_in.housing_offer_id,
        )

        if conversation_in.initial_message:
            self.repository.send_message(
                conversation.id,
                user_id,
                conversation_in.initial_message,
            )

        return ConversationRead.model_validate(conversation)

    def get_user_conversations(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> List[ConversationRead]:
        """Get all conversations for a user."""
        conversations = self.repository.get_user_conversations(user_id, skip, limit)

        result = []
        for conv in conversations:
            unread_count = self.repository.get_unread_count(conv.id, user_id)
            last_message = None
            if conv.messages:
                last_message = conv.messages[-1].content[:100]

            conv_dict = {
                "id": conv.id,
                "user1_id": conv.user1_id,
                "user2_id": conv.user2_id,
                "housing_offer_id": conv.housing_offer_id,
                "created_at": conv.created_at,
                "last_message_at": conv.last_message_at,
                "unread_count": unread_count,
                "last_message": last_message,
            }
            result.append(ConversationRead(**conv_dict))

        return result

    def get_conversation_by_id(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> ConversationDetail:
        """Get a conversation with all messages."""
        conversation = self.repository.get_by_id(conversation_id, user_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )

        self.repository.mark_messages_as_read(conversation_id, user_id)
        return ConversationDetail.model_validate(conversation)

    async def send_message(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        message: ConversationMessageCreate,
    ) -> ConversationMessageRead:
        """Send a message in a conversation."""
        conversation = self.repository.get_by_id(conversation_id, user_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )

        message_obj = self.repository.send_message(conversation_id, user_id, message.content)

        recipient_id = conversation.user2_id if conversation.user1_id == user_id else conversation.user1_id

        await ws_service.send_message_notification(
            conversation_id=conversation_id,
            recipient_id=recipient_id,
            sender_id=user_id,
            content=message.content,
        )

        return ConversationMessageRead.model_validate(message_obj)

    def get_conversation_messages(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ConversationMessageRead]:
        """Get messages from a conversation."""
        conversation = self.repository.get_by_id(conversation_id, user_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )

        messages = self.repository.get_messages(conversation_id, skip, limit)
        return [ConversationMessageRead.model_validate(msg) for msg in messages]

    def mark_conversation_read(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        """Mark all messages in a conversation as read."""
        conversation = self.repository.get_by_id(conversation_id, user_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )

        self.repository.mark_messages_as_read(conversation_id, user_id)

    def delete_conversation(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        """Delete a conversation."""
        conversation = self.repository.get_by_id(conversation_id, user_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )

        self.repository.delete(conversation)
