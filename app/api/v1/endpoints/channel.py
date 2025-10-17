import uuid
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.utils.decorators import handle_crud_errors
from app.core.database import get_db
from app.core.dependencies import require_role
from app.crud.channel import ChannelCRUD
from app.literals.users import Role
from app.schemas import ChannelCreate, ChannelRead, ChannelUpdate, MembershipRead, TokenData

router = APIRouter()


@router.get("/", response_model=List[ChannelRead])
@handle_crud_errors
def fetch_channels(db: Session = Depends(get_db), _: TokenData = Depends(require_role([Role.ADMIN]))):
    """
    Retrieve all public channels.
    Args:
        db: Session
    Returns:
        List[ChannelRead]
    """
    return ChannelCRUD.get_all(db)


@router.get("/{channel_id}", response_model=ChannelRead)
@handle_crud_errors
def fetch_channel(channel_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Retrieve a specific channel.
    """
    return ChannelCRUD.get_by_id(db, channel_id)


@router.post("/", response_model=ChannelRead)
@handle_crud_errors
def create_channel(channel: ChannelCreate, db: Session = Depends(get_db)):
    """
    Create a new channel.
    Args:
        channel (ChannelCreate): New channel.
        db (Session): Database session.
    Returns:
        ChannelRead: Created channel.
    """
    return ChannelCRUD.create(db, channel)


@router.patch("/{channel_id}", response_model=ChannelRead)
@handle_crud_errors
def update_channel(channel_id: uuid.UUID, channel: ChannelUpdate, db: Session = Depends(get_db)):
    """
    Update a specific channel.
    Args:
        channel_id (uuid.UUID): Channel id.
        channel (Channel): Channel object.
        db (Session): Database session.
    Returns:
        Channel: Updated channel object.
    """
    return ChannelCRUD.update(db, channel_id, channel)


@router.delete("/{channel_id}", response_model=bool)
@handle_crud_errors
def delete_channel(channel_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Delete a specific channel.
    Args:
        channel_id (uuid.UUID): Channel id.
        db (Session): Database session.
    Returns:
        bool: True if channel was deleted False otherwise.
    """
    return ChannelCRUD.delete(db, channel_id)


@router.post("/{channel_id}/add_member/{member_id}", response_model=MembershipRead)
@handle_crud_errors
def add_member(channel_id: uuid.UUID, member_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Add a member to a channel.
    Args:
        channel_id (uuid.UUID): Channel id.
        member_id (uuid.UUID): Member id.
        db (Session): Database session.
    Returns:
        MembershipRead: User Membership to the channel.
    """
    return ChannelCRUD.add_member(db, channel_id, member_id)


@router.post("/{channel_id}/remove_member/{member_id}", response_model=bool)
@handle_crud_errors
def remove_member(channel_id: uuid.UUID, member_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Removes a member from a channel.
    Args:
        channel_id (uuid.UUID): Channel id.
        member_id (uuid.UUID): Member id.
        db (Session): Database session.
    Returns:
        bool: True if the member was removed, False otherwise.
    """
    return ChannelCRUD.remove_member(db, channel_id, member_id)


# @router.post("/{channel_id}/ban/{member_id}", response_model=bool)
# @handle_crud_errors
# def ban(channel_id: uuid.UUID, member_id: uuid.UUID, db: Session = Depends(get_db)):
#     """
#     Bans a member from a channel.
#     Args:
#         channel_id (uuid.UUID): Channel id.
#         member_id (uuid.UUID): Member id.
#         db (Session): Database session.
#     Returns:
#         bool: True if the member was banned, False otherwise.
#     """
#     return ChannelCRUD.ban_member(db, channel_id, member_id, )
#
#
# @router.post("/{channel_id}/unban/{member_id}", response_model=bool)
# @handle_crud_errors
# def unban(channel_id: uuid.UUID, member_id: uuid.UUID, db: Session = Depends(get_db)):
#     """
#     Unbans a member from a channel.
#     Args:
#         channel_id (uuid.UUID): Channel id.
#         member_id (uuid.UUID): Member id.
#         db (Session): Database session.
#     Returns:
#         bool: True if the member was unbanned, False otherwise.
#     """
#     return ChannelCRUD.unban_member(db, channel_id, member_id)
