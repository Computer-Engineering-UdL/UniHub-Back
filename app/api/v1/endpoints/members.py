import datetime
import uuid
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette import status

from app.api.utils import handle_api_errors
from app.api.utils.permissions import get_channel_permission, is_channel_member
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.core.types import TokenData
from app.domains.channel import ChannelService
from app.literals.channels import ChannelRole
from app.literals.users import Role
from app.models import ChannelMember
from app.schemas import BanCreate, BanRead, MemberRoleUpdate, MembershipRead, UnbanCreate, UnbanRead

router = APIRouter()


async def get_channel_service(db: Session = Depends(get_db)) -> ChannelService:
    """Dependency to inject Channelawait service."""
    return ChannelService(db)


@router.post("/{channel_id}/add_member/{member_id}", response_model=MembershipRead)
@handle_api_errors()
async def add_member(
    channel_id: uuid.UUID,
    member_id: uuid.UUID,
    service: ChannelService = Depends(get_channel_service),
    _: ChannelMember = Depends(get_channel_permission(ChannelRole.ADMIN)),
):
    """Add a member to a channel. Requires channel admin role."""
    return await service.add_member(channel_id, member_id)


@router.post("/{channel_id}/remove_member/{member_id}", response_model=MembershipRead)
@handle_api_errors()
async def remove_member(
    channel_id: uuid.UUID,
    member_id: uuid.UUID,
    service: ChannelService = Depends(get_channel_service),
    _: ChannelMember = Depends(get_channel_permission(ChannelRole.MODERATOR)),
):
    """Remove a member from a channel. Requires moderator role or above."""
    return await service.remove_member(channel_id, member_id)


@router.post("/{channel_id}/set_role", response_model=MembershipRead)
@handle_api_errors()
async def set_member_role(
    channel_id: uuid.UUID,
    role_update: MemberRoleUpdate,
    service: ChannelService = Depends(get_channel_service),
    _: TokenData = Depends(require_role(Role.ADMIN)),
):
    """
    Set a member's role in a channel (e.g., promote to Moderator).
    Requires site admin role.
    """
    return await service.update_member_role(channel_id, role_update.user_id, role_update.new_role)


@router.post("/{channel_id}/join", response_model=MembershipRead)
@handle_api_errors()
async def join_channel(
    channel_id: uuid.UUID,
    service: ChannelService = Depends(get_channel_service),
    user: TokenData = Depends(get_current_user),
):
    """Join a channel. Requires registered user."""
    return await service.join_channel(channel_id, user.id, user.role)


@router.post("/{channel_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
@handle_api_errors()
async def leave_channel(
    channel_id: uuid.UUID,
    service: ChannelService = Depends(get_channel_service),
    user: TokenData = Depends(get_current_user),
):
    """Leave a channel. Requires registered user."""
    await service.leave_channel(channel_id, user.id)


@router.post("/{channel_id}/ban", response_model=BanRead)
@handle_api_errors()
async def ban_member(
    channel_id: uuid.UUID,
    ban_req: BanCreate,
    service: ChannelService = Depends(get_channel_service),
    current_user: TokenData = Depends(get_current_user),
    _: ChannelMember = Depends(get_channel_permission(ChannelRole.MODERATOR)),
):
    """Ban a member from a channel. Requires moderator role or above."""
    duration = datetime.timedelta(days=ban_req.duration_days)

    return await service.ban_member(
        channel_id=channel_id,
        user_id=ban_req.user_id,
        motive=ban_req.motive,
        duration=duration,
        banned_by=current_user.id,
    )


@router.post("/{channel_id}/unban", response_model=UnbanRead)
@handle_api_errors()
async def unban_member(
    channel_id: uuid.UUID,
    unban_req: UnbanCreate,
    service: ChannelService = Depends(get_channel_service),
    current_user: TokenData = Depends(get_current_user),
    _: ChannelMember = Depends(get_channel_permission(ChannelRole.MODERATOR)),
):
    """Unban a member from a channel. Requires moderator role or above."""
    return await service.unban_member(
        channel_id=channel_id,
        user_id=unban_req.user_id,
        motive=unban_req.motive,
        unbanned_by=current_user.id,
    )


@router.get("/{channel_id}/member/{user_id}/", response_model=MembershipRead)
async def get_member(
    channel_id: uuid.UUID,
    user_id: uuid.UUID,
    service: ChannelService = Depends(get_channel_service),
    _: ChannelMember = Depends(is_channel_member),
):
    """Get a specific member's info. Must be a channel member."""
    return await service.get_member(channel_id, user_id)


@router.get("/{channel_id}/members", response_model=List[MembershipRead])
def get_members(
    channel_id: uuid.UUID,
    service: ChannelService = Depends(get_channel_service),
    _: ChannelMember = Depends(is_channel_member),
):
    """Get channel member list."""
    return service.get_members(channel_id)
