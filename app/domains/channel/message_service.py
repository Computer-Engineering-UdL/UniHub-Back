import uuid
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session
from starlette import status

from app.domains.channel import ChannelRepository
from app.domains.channel.message_repository import MessageRepository
from app.domains.websocket.websocket_service import ws_service
from app.literals.users import ROLE_HIERARCHY, Role
from app.schemas.message import MessageCreate, MessageRead, MessageUpdate


class MessageService:
    """Service layer for message-related business logic."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = MessageRepository(db)
        self.channel_repository = ChannelRepository(db)

    async def send_message(self, message_in: MessageCreate, user_role: Role) -> MessageRead:
        """Send a message to a channel."""

        channel = self.channel_repository.get_by_id(message_in.channel_id)
        if not channel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Channel not found",
            )

        user_level = ROLE_HIERARCHY.get(user_role, 99)
        channel_read_level = ROLE_HIERARCHY[channel.required_role_read]

        if user_level > channel_read_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this channel",
            )

        channel_write_level = ROLE_HIERARCHY[channel.required_role_write]
        if user_level > channel_write_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to write in this channel",
            )

        message_data = message_in.model_dump()
        message = self.repository.create(message_data)

        await ws_service.send_channel_message(
            channel_id=message_in.channel_id,
            message_id=message.id,
            user_id=message_in.user_id,
            content=message.content,
        )

        return MessageRead.model_validate(message)

    def get_message_by_id(self, message_id: uuid.UUID) -> MessageRead:
        """Get a message by ID."""
        message = self.repository.get_by_id(message_id)
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found",
            )
        return MessageRead.model_validate(message)

    def get_channel_messages(
        self,
        channel_id: uuid.UUID,
        user_role: Optional[Role] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[MessageRead]:
        """Get all messages from a channel."""

        channel = self.channel_repository.get_by_id(channel_id)
        if not channel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Channel not found",
            )

        user_level = ROLE_HIERARCHY.get(user_role or Role.BASIC, ROLE_HIERARCHY[Role.BASIC])
        channel_read_level = ROLE_HIERARCHY[channel.required_role_read]

        if user_level > channel_read_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to read messages in this channel",
            )

        messages = self.repository.get_channel_messages(channel_id, skip, limit)
        return [MessageRead.model_validate(msg) for msg in messages]

    async def update_message(self, message_id: uuid.UUID, message_update: MessageUpdate) -> MessageRead:
        """Update a message."""
        message = self.repository.get_by_id(message_id)
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found",
            )

        update_data = message_update.model_dump(exclude_unset=True)
        updated_message = self.repository.update(message_id, update_data)

        if not updated_message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found",
            )

        await ws_service.send_message_update(
            channel_id=message.channel_id,
            message_id=message.id,
            content=updated_message.content,
        )

        return MessageRead.model_validate(updated_message)

    async def delete_message(self, message_id: uuid.UUID) -> None:
        """Delete a message."""
        message = self.repository.get_by_id(message_id)
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found",
            )

        channel_id = message.channel_id
        self.repository.delete(message)

        await ws_service.send_message_delete(
            channel_id=channel_id,
            message_id=message_id,
        )

    async def reply_to_message(self, parent_message_id: uuid.UUID, reply_data: dict, user_role: Role) -> MessageRead:
        """Reply to a message."""

        parent = self.repository.get_by_id(parent_message_id)
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found",
            )

        channel = self.channel_repository.get_by_id(parent.channel_id)
        if not channel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Channel not found",
            )

        user_level = ROLE_HIERARCHY.get(user_role, 99)
        channel_write_level = ROLE_HIERARCHY[channel.required_role_write]

        if user_level > channel_write_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to write in this channel",
            )

        reply = self.repository.create_reply(parent_message_id, reply_data)
        if not reply:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found in this channel",
            )

        await ws_service.send_message_reply(
            channel_id=parent.channel_id,
            message_id=reply.id,
            parent_message_id=parent_message_id,
            user_id=reply.user_id,
            content=reply.content,
        )

        return MessageRead.model_validate(reply)

    def verify_message_in_channel(self, message_id: uuid.UUID, channel_id: uuid.UUID) -> None:
        """Verify a message belongs to a specific channel."""
        message = self.repository.get_by_id(message_id)
        if not message or message.channel_id != channel_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found in this channel",
            )
