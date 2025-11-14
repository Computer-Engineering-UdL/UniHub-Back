import uuid
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette import status

from app.api.utils.decorators import handle_api_errors
from app.api.utils.permissions import get_channel_permission
from app.core.database import get_db
from app.core.dependencies import get_optional_current_user, require_role
from app.core.types import TokenData
from app.domains.channel import ChannelService
from app.literals.channels import ChannelRole
from app.literals.users import Role
from app.models import ChannelMember
from app.schemas import (
    ChannelCreate,
    ChannelDetail,
    ChannelRead,
    ChannelReadWithCount,
    ChannelUpdate,
)

router = APIRouter()


def get_channel_service(db: Session = Depends(get_db)) -> ChannelService:
    """Dependency to inject ChannelService."""
    return ChannelService(db)


@router.get("/", response_model=List[ChannelReadWithCount])
def fetch_channels(
    service: ChannelService = Depends(get_channel_service),
    user: TokenData | None = Depends(get_optional_current_user),
):
    """
    Retrieve all channels visible to the current user (including anonymous).
    Admins see all channels. Others see based on 'required_role_read'.
    """
    is_admin = user and user.role == Role.ADMIN
    user_role = user.role if user else None

    return service.list_channels(user_role=user_role, is_admin=is_admin)


@router.get("/{channel_id}", response_model=ChannelDetail)
@handle_api_errors()
def fetch_channel(
    channel_id: uuid.UUID,
    service: ChannelService = Depends(get_channel_service),
    user: TokenData | None = Depends(get_optional_current_user),
):
    """
    Retrieve a specific channel.
    Access is based on the channel's 'required_role_read'.
    """
    user_role = user.role if user else None

    if not service.check_read_permission(channel_id, user_role):
        from fastapi import HTTPException

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this channel",
        )

    return service.get_channel_by_id(channel_id)


@router.post("/", response_model=ChannelRead)
@handle_api_errors()
def create_channel(
    channel: ChannelCreate,
    service: ChannelService = Depends(get_channel_service),
    user: TokenData = Depends(require_role(Role.ADMIN)),
):
    """Create a new channel. Site Admin only. Creator becomes channel admin."""
    return service.create_channel(channel, user.id)


@router.patch("/{channel_id}", response_model=ChannelRead)
@handle_api_errors()
def update_channel(
    channel_id: uuid.UUID,
    channel: ChannelUpdate,
    service: ChannelService = Depends(get_channel_service),
    _: ChannelMember = Depends(get_channel_permission(ChannelRole.ADMIN)),
):
    """Update a channel. Requires channel admin role."""
    return service.update_channel(channel_id, channel)


@router.delete("/{channel_id}", response_model=bool)
@handle_api_errors()
def delete_channel(
    channel_id: uuid.UUID,
    service: ChannelService = Depends(get_channel_service),
    _: TokenData = Depends(require_role(Role.ADMIN)),
):
    """Delete a channel. Requires site admin role."""
    return service.delete_channel(channel_id)
