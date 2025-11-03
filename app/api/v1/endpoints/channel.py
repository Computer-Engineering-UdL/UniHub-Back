import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette import status

from app.api.utils.decorators import handle_api_errors
from app.api.utils.permissions import get_channel_permission
from app.core.database import get_db
from app.core.dependencies import get_optional_current_user, require_role
from app.core.types import TokenData
from app.crud.channel import ChannelCRUD
from app.literals.channels import ChannelRole
from app.literals.users import ROLE_HIERARCHY, Role
from app.models import ChannelMember
from app.schemas import (
    ChannelCreate,
    ChannelRead,
    ChannelUpdate,
)

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
