import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from starlette import status

from app.api.utils import handle_api_errors
from app.api.utils.permissions import get_channel_permission
from app.core import get_db
from app.core.dependencies import get_current_user, get_optional_current_user
from app.core.types import TokenData
from app.crud.channel import ChannelCRUD
from app.crud.messages import MessagesCRUD
from app.literals.channels import ChannelRole
from app.literals.users import ROLE_HIERARCHY, Role
from app.models import ChannelMember
from app.schemas import MessageAnswer, MessageCreate, MessageRead, MessageUpdate

router = APIRouter()


@router.post("/{channel_id}/messages", response_model=MessageRead)
@handle_api_errors()
def send_message(
    channel_id: uuid.UUID,
    message: MessageCreate,
    db: Session = Depends(get_db),
    user: TokenData = Depends(get_current_user),
):
    """
    Send a new message to a channel.
    Requires user to have 'write' permission for this channel.
    """
    channel_db = ChannelCRUD.get_by_id(db, channel_id)
    if not channel_db:
        raise HTTPException(status_code=404, detail="Channel not found")
    user_level = ROLE_HIERARCHY.get(user.role, 99)
    channel_read_level = ROLE_HIERARCHY[channel_db.required_role_read]
    if user_level > channel_read_level:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this channel",
        )
    channel_write_level = ROLE_HIERARCHY[channel_db.required_role_write]
    if user_level > channel_write_level:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to write in this channel",
        )
    message.channel_id = channel_id
    message.user_id = user.id
    return MessagesCRUD.send_message(db, message)


@router.get("/{channel_id}/messages", response_model=List[MessageRead])
@handle_api_errors()
def get_channel_messages(
    channel_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    user: TokenData | None = Depends(get_optional_current_user),
):
    """
    Retrieve all messages from a channel.
    Access is based on the channel's 'required_role_read'.
    """
    channel_db = ChannelCRUD.get_by_id(db, channel_id)
    if not channel_db:
        raise HTTPException(status_code=404, detail="Channel not found")
    user_level = ROLE_HIERARCHY[Role.BASIC]
    if user:
        user_level = ROLE_HIERARCHY.get(user.role, user_level)
    channel_read_level = ROLE_HIERARCHY[channel_db.required_role_read]
    if user_level > channel_read_level:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to read messages in this channel",
        )
    return MessagesCRUD.get_channel_messages(db, channel_id, skip, limit)


@router.get("/{channel_id}/messages/{message_id}", response_model=MessageRead)
@handle_api_errors()
def fetch_message(
    channel_id: uuid.UUID,
    message_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: TokenData | None = Depends(get_optional_current_user),
):
    """
    Retrieve a single message.
    Access is based on the channel's 'required_role_read'.
    """
    channel_db = ChannelCRUD.get_by_id(db, channel_id)
    if not channel_db:
        raise HTTPException(status_code=404, detail="Channel not found")
    user_level = ROLE_HIERARCHY[Role.BASIC]
    if user:
        user_level = ROLE_HIERARCHY.get(user.role, user_level)
    channel_read_level = ROLE_HIERARCHY[channel_db.required_role_read]
    if user_level > channel_read_level:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to read this channel",
        )
    message = MessagesCRUD.get_message_by_id(db, message_id)
    if message.channel_id != channel_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found in this channel",
        )
    return message


@router.put("/{channel_id}/messages/{message_id}", response_model=MessageRead)
@handle_api_errors()
def update_message(
    channel_id: uuid.UUID,
    message_id: uuid.UUID,
    message_update: MessageUpdate,
    db: Session = Depends(get_db),
    channel_member: ChannelMember = Depends(get_channel_permission(ChannelRole.ADMIN)),
):
    """
    Update a message. Channel admin only.
    URL: PUT /api/v1/channel/{channel_id}/messages/{message_id}
    """
    existing_message = MessagesCRUD.get_message_by_id(db, message_id)
    if existing_message.channel_id != channel_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found in this channel",
        )

    return MessagesCRUD.update_message(db, message_id, message_update)


@router.delete("/{channel_id}/messages/{message_id}", status_code=204)
@handle_api_errors()
def delete_message(
    channel_id: uuid.UUID,
    message_id: uuid.UUID,
    db: Session = Depends(get_db),
    channel_member: ChannelMember = Depends(get_channel_permission(ChannelRole.MODERATOR)),
):
    """
    Delete a message. Requires channel moderator role or above.
    """
    message = MessagesCRUD.get_message_by_id(db, message_id)
    if message.channel_id != channel_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found in this channel",
        )
    MessagesCRUD.delete_message(db, message)


@router.post("/{channel_id}/messages/{message_id}/reply", response_model=MessageRead)
@handle_api_errors()
def post_reply(
    channel_id: uuid.UUID,
    message_id: uuid.UUID,
    reply: MessageAnswer,
    db: Session = Depends(get_db),
    user: TokenData = Depends(get_current_user),
):
    """
    Reply to a message.
    Requires user to have 'write' permission for this channel.
    """
    channel_db = ChannelCRUD.get_by_id(db, channel_id)
    if not channel_db:
        raise HTTPException(status_code=404, detail="Channel not found")
    user_level = ROLE_HIERARCHY.get(user.role, 99)
    channel_write_level = ROLE_HIERARCHY[channel_db.required_role_write]
    if user_level > channel_write_level:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to write in this channel",
        )
    parent_message = MessagesCRUD.get_message_by_id(db, message_id)
    if parent_message.channel_id != channel_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found in this channel",
        )
    reply.channel_id = channel_id
    reply.parent_message_id = message_id
    reply.user_id = user.id
    return MessagesCRUD.answer_to_message(db, reply)
