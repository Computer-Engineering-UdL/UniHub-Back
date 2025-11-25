import datetime
import uuid
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette import status

from app.domains.channel import ChannelRepository
from app.domains.websocket.websocket_service import ws_service
from app.literals.channels import ChannelRole
from app.literals.users import ROLE_HIERARCHY, Role
from app.schemas.channel import (
    BanRead,
    ChannelCreate,
    ChannelDetail,
    ChannelRead,
    ChannelReadWithCount,
    ChannelUpdate,
    MembershipRead,
    UnbanRead,
)


class ChannelService:
    """Service layer for channel-related business logic."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = ChannelRepository(db)

    async def create_channel(self, channel_in: ChannelCreate, creator_id: uuid.UUID) -> ChannelRead:
        """Create a new channel and add creator as admin."""
        try:
            channel_data = channel_in.model_dump()
            channel = self.repository.create(channel_data)
            self.repository.add_member(channel.id, creator_id, role=ChannelRole.ADMIN)

            await ws_service.send_channel_created(
                channel_id=channel.id,
                channel_name=channel.name,
            )

            return ChannelRead.model_validate(channel)
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Channel with this name already exists",
            )

    def get_channel_by_id(self, channel_id: uuid.UUID) -> ChannelDetail:
        """Get a channel by ID with full details."""
        channel = self.repository.get_by_id(channel_id)
        if not channel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Channel not found",
            )
        return ChannelDetail.model_validate(channel)

    def list_channels(
        self,
        user_role: Optional[Role] = None,
        is_admin: bool = False,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ChannelReadWithCount]:
        """List all channels visible to the user."""
        if is_admin:
            channels = self.repository.get_all(skip=skip, limit=limit)
        else:
            user_level = ROLE_HIERARCHY.get(user_role or Role.BASIC, ROLE_HIERARCHY[Role.BASIC])
            channels = self.repository.get_public_channels(user_level, skip, limit)

        return [ChannelReadWithCount.model_validate(ch) for ch in channels]

    async def update_channel(self, channel_id: uuid.UUID, channel_in: ChannelUpdate) -> ChannelRead:
        """Update a channel."""
        update_data = channel_in.model_dump(exclude_unset=True)
        channel = self.repository.update(channel_id, update_data)

        if not channel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Channel not found",
            )

        await ws_service.send_channel_updated(
            channel_id=channel_id,
            updated_fields=update_data,
        )

        return ChannelRead.model_validate(channel)

    async def delete_channel(self, channel_id: uuid.UUID) -> bool:
        """Delete a channel."""
        channel = self.repository.get_by_id(channel_id)
        if not channel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Channel not found",
            )

        await ws_service.send_channel_deleted(channel_id=channel_id)

        self.repository.delete(channel)
        return True

    async def add_member(
        self, channel_id: uuid.UUID, user_id: uuid.UUID, role: ChannelRole = ChannelRole.USER
    ) -> MembershipRead:
        """Add a member to a channel."""
        membership = self.repository.add_member(channel_id, user_id, role)
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Channel not found",
            )

        await ws_service.send_member_joined(
            channel_id=channel_id,
            user_id=user_id,
        )

        return MembershipRead.model_validate(membership)

    async def remove_member(self, channel_id: uuid.UUID, user_id: uuid.UUID) -> MembershipRead:
        """Remove a member from a channel."""
        membership = self.repository.remove_member(channel_id, user_id)
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found",
            )

        await ws_service.send_user_kicked(
            channel_id=channel_id,
            user_id=user_id,
        )

        return MembershipRead.model_validate(membership)

    async def update_member_role(
        self, channel_id: uuid.UUID, user_id: uuid.UUID, new_role: ChannelRole
    ) -> MembershipRead:
        """Update a member's role in a channel."""
        membership = self.repository.update_member_role(channel_id, user_id, new_role)
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found in this channel",
            )

        await ws_service.send_member_role_updated(
            channel_id=channel_id,
            user_id=user_id,
            new_role=new_role.value,
        )

        return MembershipRead.model_validate(membership)

    def get_member(self, channel_id: uuid.UUID, user_id: uuid.UUID) -> MembershipRead:
        """Get a specific member's info."""
        membership = self.repository.get_member(channel_id, user_id)
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found",
            )
        return MembershipRead.model_validate(membership)

    def get_members(self, channel_id: uuid.UUID) -> List[MembershipRead]:
        """Get all members of a channel."""
        members = self.repository.get_members(channel_id)
        if members is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Channel not found",
            )
        return [MembershipRead.model_validate(m) for m in members]

    async def join_channel(self, channel_id: uuid.UUID, user_id: uuid.UUID, user_role: Role) -> MembershipRead:
        """Join a channel as a user."""
        channel = self.repository.get_by_id(channel_id)
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
                detail="You do not have permission to join this channel",
            )

        existing = self.repository.get_member(channel_id, user_id)
        if existing:
            if existing.is_banned:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are banned from this channel",
                )
            return MembershipRead.model_validate(existing)

        membership = self.repository.add_member(channel_id, user_id, ChannelRole.USER)

        await ws_service.send_member_joined(
            channel_id=channel_id,
            user_id=user_id,
        )

        return MembershipRead.model_validate(membership)

    async def leave_channel(self, channel_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Leave a channel."""
        membership = self.repository.remove_member(channel_id, user_id)
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="You are not a member of this channel",
            )

        await ws_service.send_member_left(
            channel_id=channel_id,
            user_id=user_id,
        )

    async def ban_member(
        self, channel_id: uuid.UUID, user_id: uuid.UUID, motive: str, duration: datetime.timedelta, banned_by: uuid.UUID
    ) -> BanRead:
        """Ban a member from a channel."""
        ban = self.repository.ban_member(
            channel_id=channel_id,
            user_id=user_id,
            motive=motive,
            duration=duration,
            banned_by=banned_by,
        )

        if not ban:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Channel or member not found",
            )

        await ws_service.send_user_banned(
            channel_id=channel_id,
            user_id=user_id,
            motive=motive,
        )

        return BanRead.model_validate(ban)

    async def unban_member(
        self, channel_id: uuid.UUID, user_id: uuid.UUID, motive: str, unbanned_by: uuid.UUID
    ) -> UnbanRead:
        """Unban a member from a channel."""
        unban = self.repository.unban_member(
            channel_id=channel_id,
            user_id=user_id,
            motive=motive,
            unbanned_by=unbanned_by,
        )

        if not unban:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Channel not found",
            )

        await ws_service.send_user_unbanned(
            channel_id=channel_id,
            user_id=user_id,
            motive=motive,
        )

        return UnbanRead.model_validate(unban)

    def check_read_permission(self, channel_id: uuid.UUID, user_role: Optional[Role] = None) -> bool:
        """Check if a user has permission to read a channel."""
        channel = self.repository.get_by_id(channel_id)
        if not channel:
            return False

        user_level = ROLE_HIERARCHY.get(user_role or Role.BASIC, ROLE_HIERARCHY[Role.BASIC])
        channel_read_level = ROLE_HIERARCHY[channel.required_role_read]

        return user_level <= channel_read_level

    def check_write_permission(self, channel_id: uuid.UUID, user_role: Role) -> bool:
        """Check if a user has permission to write in a channel."""
        channel = self.repository.get_by_id(channel_id)
        if not channel:
            return False

        user_level = ROLE_HIERARCHY.get(user_role, 99)
        channel_write_level = ROLE_HIERARCHY[channel.required_role_write]

        return user_level <= channel_write_level
