import datetime
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette import status

from app.api.utils.decorators import handle_api_errors
from app.api.utils.permissions import get_channel_permission, is_channel_member
from app.core.database import get_db
from app.core.dependencies import get_current_user, get_optional_current_user, require_role
from app.core.types import TokenData
from app.crud.channel import ChannelCRUD
from app.crud.messages import MessagesCRUD
from app.literals.channels import ChannelRole
from app.literals.users import ROLE_HIERARCHY, Role
from app.models import ChannelMember
from app.schemas import (
    BanCreate,
    BanRead,
    ChannelCreate,
    ChannelRead,
    ChannelUpdate,
    MembershipRead,
    MessageAnswer,
    MessageCreate,
    MessageRead,
    MessageUpdate,
)
from app.schemas.channel import UnbanCreate, UnbanRead

router = APIRouter()


@router.get("/", response_model=List[ChannelRead])
def fetch_channels(
    db: Session = Depends(get_db),
    user: TokenData | None = Depends(get_optional_current_user),
):
    """
    Retrieve all channels visible to the current user (including anonymous).
    Admins see all channels. Others see based on 'required_role_read'.
    """
    if user and user.role == Role.ADMIN:
        return ChannelCRUD.get_all(db)

    user_level = ROLE_HIERARCHY[Role.BASIC]
    if user:
        user_level = ROLE_HIERARCHY.get(user.role, user_level)

    return ChannelCRUD.get_public_channels(db, user_level)


@router.get("/{channel_id}", response_model=ChannelRead)
@handle_api_errors()
def fetch_channel(
    channel_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: TokenData | None = Depends(get_optional_current_user),
):
    """
    Retrieve a specific channel.
    Access is based on the channel's 'required_role_read'.
    """
    channel_db = ChannelCRUD.get_by_id(db, channel_id)
    if not channel_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found")
    user_level = ROLE_HIERARCHY[Role.BASIC]
    if user:
        user_level = ROLE_HIERARCHY.get(user.role, user_level)
    channel_read_level = ROLE_HIERARCHY[channel_db.required_role_read]
    if user_level > channel_read_level:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this channel",
        )
    return ChannelRead.model_validate(channel_db)


@router.post("/", response_model=ChannelRead)
@handle_api_errors()
def create_channel(
    channel: ChannelCreate,
    db: Session = Depends(get_db),
    user: TokenData = Depends(require_role(Role.ADMIN)),
):
    """Create a new channel. Site Admin only. Creator becomes channel admin."""
    new_channel = ChannelCRUD.create(db, channel)
    channel_id = uuid.UUID(str(new_channel.id))
    ChannelCRUD.add_member(db, channel_id, uuid.UUID(str(user.id)), role=ChannelRole.ADMIN)

    return new_channel


@router.patch("/{channel_id}", response_model=ChannelRead)
@handle_api_errors()
def update_channel(
    channel_id: uuid.UUID,
    channel: ChannelUpdate,
    db: Session = Depends(get_db),
    _: ChannelMember = Depends(get_channel_permission(ChannelRole.ADMIN)),
):
    """Update a channel. Requires channel admin role."""
    return ChannelCRUD.update(db, channel_id, channel)


@router.delete("/{channel_id}", response_model=bool)
@handle_api_errors()
def delete_channel(
    channel_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: TokenData = Depends(require_role(Role.ADMIN)),
):
    """Delete a channel. Requires site admin role."""
    result = ChannelCRUD.delete(db, channel_id)
    return result is not None


@router.post("/{channel_id}/add_member/{member_id}", response_model=MembershipRead)
@handle_api_errors()
def add_member(
    channel_id: uuid.UUID,
    member_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: ChannelMember = Depends(get_channel_permission(ChannelRole.ADMIN)),
):
    """Add a member to a channel. Requires channel admin role."""
    return ChannelCRUD.add_member(db, channel_id, member_id)


@router.post("/{channel_id}/remove_member/{member_id}", response_model=MembershipRead)
@handle_api_errors()
def remove_member(
    channel_id: uuid.UUID,
    member_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: ChannelMember = Depends(get_channel_permission(ChannelRole.MODERATOR)),
):
    """Remove a member from a channel. Requires moderator role or above."""
    removed = ChannelCRUD.remove_member(db, channel_id, member_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Member not found")
    return removed


class MemberRoleUpdate(BaseModel):
    user_id: uuid.UUID
    new_role: ChannelRole


@router.post("/{channel_id}/set_role", response_model=MembershipRead)
@handle_api_errors()
def set_member_role(
    channel_id: uuid.UUID,
    role_update: MemberRoleUpdate,
    db: Session = Depends(get_db),
    _: TokenData = Depends(require_role(Role.ADMIN)),
):
    """
    Set a member's role in a channel (e.g., promote to Moderator).
    Requires site admin role.
    """
    updated_member = ChannelCRUD.update_member_role(db, channel_id, role_update.user_id, role_update.new_role)
    if not updated_member:
        raise HTTPException(status_code=404, detail="User not found in this channel")
    return updated_member


@router.post("/{channel_id}/join", response_model=MembershipRead)
@handle_api_errors()
def join_channel(
    channel_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: TokenData = Depends(get_current_user),
):
    """Join a channel. Requires registered user."""
    channel_db = ChannelCRUD.get_by_id(db, channel_id)
    if not channel_db:
        raise HTTPException(status_code=404, detail="Channel not found")
    user_level = ROLE_HIERARCHY.get(user.role, 99)
    channel_read_level = ROLE_HIERARCHY[channel_db.required_role_read]
    if user_level > channel_read_level:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to join this channel",
        )
    existing = ChannelCRUD.get_member(db, channel_id, user.id)
    if existing:
        if existing.is_banned:
            raise HTTPException(status_code=403, detail="You are banned from this channel")
        return existing
    return ChannelCRUD.add_member(db, channel_id, user.id, role=ChannelRole.USER)


@router.post("/{channel_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
@handle_api_errors()
def leave_channel(
    channel_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: TokenData = Depends(get_current_user),
):
    """Leave a channel. Requires registered user."""
    removed = ChannelCRUD.remove_member(db, channel_id, user.id)
    if not removed:
        raise HTTPException(status_code=404, detail="You are not a member of this channel")
    return None


@router.post("/{channel_id}/ban", response_model=BanRead)
@handle_api_errors()
def ban_member(
    channel_id: uuid.UUID,
    ban_req: BanCreate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
    _: ChannelMember = Depends(get_channel_permission(ChannelRole.MODERATOR)),
):
    """Ban a member from a channel. Requires moderator role or above."""
    duration = datetime.timedelta(days=ban_req.duration_days)

    banned = ChannelCRUD.ban_member(
        db=db,
        channel_id=channel_id,
        user_id=ban_req.user_id,
        motive=ban_req.motive,
        duration=duration,
        banned_by=current_user.id,
    )

    if not banned:
        raise HTTPException(status_code=404, detail="Channel or member not found")

    return banned


@router.post("/{channel_id}/unban", response_model=UnbanRead)
@handle_api_errors()
def unban_member(
    channel_id: uuid.UUID,
    unban_req: UnbanCreate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
    _: ChannelMember = Depends(get_channel_permission(ChannelRole.MODERATOR)),
):
    """Unban a member from a channel. Requires moderator role or above."""
    unbanned = ChannelCRUD.unban_member(
        db=db,
        channel_id=channel_id,
        user_id=unban_req.user_id,
        motive=unban_req.motive,
        unbanned_by=current_user.id,
    )

    if not unbanned:
        raise HTTPException(status_code=404, detail="Channel not found")

    return unbanned


@router.get("/{channel_id}/member/{user_id}/", response_model=MembershipRead)
def get_member(
    channel_id: uuid.UUID,
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: ChannelMember = Depends(is_channel_member),
):
    """Get a specific member's info. Must be a channel member."""
    membership = ChannelCRUD.get_member(db, channel_id, user_id)
    if not membership:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    return MembershipRead.model_validate(membership)


@router.get("/{channel_id}/members", response_model=List[MembershipRead])
def get_members(
    channel_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: ChannelMember = Depends(is_channel_member),
):
    """Get channel member list"""
    memberships = ChannelCRUD.get_members(db, channel_id)
    if not memberships:
        return []
    return [MembershipRead.model_validate(membership) for membership in memberships]


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
