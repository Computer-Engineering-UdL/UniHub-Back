import datetime
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette import status

from app.api.utils.decorators import handle_crud_errors
from app.core.database import get_db
from app.core.dependencies import get_channel_permission, get_current_user, is_channel_member, require_role
from app.crud.channel import ChannelCRUD
from app.literals.channels import ChannelRole
from app.literals.users import Role
from app.models import ChannelMember
from app.schemas import BanCreate, BanRead, ChannelCreate, ChannelRead, ChannelUpdate, MembershipRead, TokenData
from app.schemas.channel import UnbanCreate, UnbanRead

router = APIRouter()


@router.get("/")
def fetch_channels(db: Session = Depends(get_db), _: TokenData = Depends(require_role(Role.ADMIN))):
    """Retrieve all channels. Admin only."""
    return ChannelCRUD.get_all(db)


@router.get("/{channel_id}", response_model=ChannelRead)
@handle_crud_errors
def fetch_channel(channel_id: uuid.UUID, db: Session = Depends(get_db), _: ChannelMember = Depends(is_channel_member)):
    """Retrieve a specific channel. Must be a member."""
    channel_db = ChannelCRUD.get_by_id(db, channel_id)
    if not channel_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found")
    return ChannelRead.model_validate(channel_db)


@router.post("/", response_model=ChannelRead)
@handle_crud_errors
def create_channel(channel: ChannelCreate, db: Session = Depends(get_db), user: TokenData = Depends(get_current_user)):
    """Create a new channel. Creator becomes channel admin."""
    new_channel = ChannelCRUD.create(db, channel)
    channel_id = uuid.UUID(str(new_channel.id))
    ChannelCRUD.add_member(db, channel_id, uuid.UUID(str(user.id)), role=ChannelRole.ADMIN)

    return new_channel


@router.patch("/{channel_id}", response_model=ChannelRead)
@handle_crud_errors
def update_channel(
    channel_id: uuid.UUID,
    channel: ChannelUpdate,
    db: Session = Depends(get_db),
    _: ChannelMember = Depends(get_channel_permission(ChannelRole.ADMIN)),
):
    """Update a channel. Requires channel admin role."""
    return ChannelCRUD.update(db, channel_id, channel)


@router.delete("/{channel_id}", response_model=bool)
@handle_crud_errors
def delete_channel(
    channel_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: ChannelMember = Depends(get_channel_permission(ChannelRole.ADMIN)),
):
    """Delete a channel. Requires channel admin role."""
    result = ChannelCRUD.delete(db, channel_id)
    return result is not None


@router.post("/{channel_id}/add_member/{member_id}", response_model=MembershipRead)
@handle_crud_errors
def add_member(
    channel_id: uuid.UUID,
    member_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: ChannelMember = Depends(get_channel_permission(ChannelRole.ADMIN)),
):
    """Add a member to a channel. Requires channel admin role."""
    return ChannelCRUD.add_member(db, channel_id, member_id)


@router.post("/{channel_id}/remove_member/{member_id}", response_model=MembershipRead)
@handle_crud_errors
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


@router.post("/{channel_id}/ban", response_model=BanRead)
@handle_crud_errors
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
@handle_crud_errors
def unban_member(
    channel_id: uuid.UUID,
    unban_req: UnbanCreate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
    _: ChannelMember = Depends(get_channel_permission(ChannelRole.MODERATOR)),
):
    """Unban a member from a channel. Requires moderator role or above."""
    unbanned = ChannelCRUD.unban_member(
        db=db, channel_id=channel_id, user_id=unban_req.user_id, motive=unban_req.motive, unbanned_by=current_user.id
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
def get_members(channel_id: uuid.UUID, db: Session = Depends(get_db), _: ChannelMember = Depends(is_channel_member)):
    """Get channel member list"""
    memberships = ChannelCRUD.get_members(db, channel_id)
    if not memberships:
        return []
    return [MembershipRead.model_validate(membership) for membership in memberships]
