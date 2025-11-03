import datetime
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette import status

from app.api.utils import handle_api_errors
from app.api.utils.permissions import get_channel_permission, is_channel_member
from app.core import get_db
from app.core.dependencies import get_current_user, require_role
from app.core.types import TokenData
from app.crud.channel import ChannelCRUD
from app.literals.channels import ChannelRole
from app.literals.users import ROLE_HIERARCHY, Role
from app.models import ChannelMember
from app.schemas import BanCreate, BanRead, MemberRoleUpdate, MembershipRead, UnbanCreate, UnbanRead

router = APIRouter()


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
    return membership


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
    return memberships
