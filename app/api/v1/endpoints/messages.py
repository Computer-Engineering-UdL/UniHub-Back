import uuid
from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from starlette import status

from app.api.utils import handle_api_errors
from app.api.utils.permissions import get_channel_permission
from app.core.database import get_db
from app.core.dependencies import get_current_user, get_optional_current_user
from app.core.types import TokenData
from app.domains.channel.message_service import MessageService
from app.literals.channels import ChannelRole
from app.models import ChannelMember
from app.schemas import MessageAnswer, MessageCreate, MessageRead, MessageUpdate

router = APIRouter()


def get_message_service(db: Session = Depends(get_db)) -> MessageService:
    """Dependency to inject MessageService."""
    return MessageService(db)


@router.post("/{channel_id}/messages", response_model=MessageRead)
@handle_api_errors()
def send_message(
    channel_id: uuid.UUID,
    message: MessageCreate,
    service: MessageService = Depends(get_message_service),
    user: TokenData = Depends(get_current_user),
):
    """
    Send a new message to a channel.
    Requires user to have 'write' permission for this channel.
    """
    message.channel_id = channel_id
    message.user_id = user.id
    return service.send_message(message, user.role)


@router.get("/{channel_id}/messages", response_model=List[MessageRead])
@handle_api_errors()
def get_channel_messages(
    channel_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    service: MessageService = Depends(get_message_service),
    user: TokenData | None = Depends(get_optional_current_user),
):
    """
    Retrieve all messages from a channel.
    Access is based on the channel's 'required_role_read'.
    """
    user_role = user.role if user else None
    return service.get_channel_messages(channel_id, user_role, skip, limit)


@router.get("/{channel_id}/messages/{message_id}", response_model=MessageRead)
@handle_api_errors()
def fetch_message(
    channel_id: uuid.UUID,
    message_id: uuid.UUID,
    service: MessageService = Depends(get_message_service),
    user: TokenData | None = Depends(get_optional_current_user),
):
    """
    Retrieve a single message.
    Access is based on the channel's 'required_role_read'.
    """
    user_role = user.role if user else None
    message = service.get_message_by_id(message_id)
    service.verify_message_in_channel(message_id, channel_id)
    service.get_channel_messages(channel_id, user_role, skip=0, limit=1)

    return message


@router.put("/{channel_id}/messages/{message_id}", response_model=MessageRead)
@handle_api_errors()
def update_message(
    channel_id: uuid.UUID,
    message_id: uuid.UUID,
    message_update: MessageUpdate,
    service: MessageService = Depends(get_message_service),
    _: ChannelMember = Depends(get_channel_permission(ChannelRole.ADMIN)),
):
    """
    Update a message. Channel admin only.
    """

    service.verify_message_in_channel(message_id, channel_id)

    return service.update_message(message_id, message_update)


@router.delete("/{channel_id}/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
@handle_api_errors()
def delete_message(
    channel_id: uuid.UUID,
    message_id: uuid.UUID,
    service: MessageService = Depends(get_message_service),
    _: ChannelMember = Depends(get_channel_permission(ChannelRole.MODERATOR)),
):
    """
    Delete a message. Requires channel moderator role or above.
    """

    service.verify_message_in_channel(message_id, channel_id)

    service.delete_message(message_id)


@router.post("/{channel_id}/messages/{message_id}/reply", response_model=MessageRead)
@handle_api_errors()
def post_reply(
    channel_id: uuid.UUID,
    message_id: uuid.UUID,
    reply: MessageAnswer,
    service: MessageService = Depends(get_message_service),
    user: TokenData = Depends(get_current_user),
):
    """
    Reply to a message.
    Requires user to have 'write' permission for this channel.
    """

    service.verify_message_in_channel(message_id, channel_id)

    reply_data = {
        "content": reply.content,
        "channel_id": channel_id,
        "user_id": user.id,
    }

    return service.reply_to_message(message_id, reply_data, user.role)
