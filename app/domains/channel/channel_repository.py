import datetime
import uuid
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.literals.channels import ChannelRole
from app.literals.users import ROLE_HIERARCHY
from app.models import Channel, ChannelBan, ChannelMember, ChannelUnban
from app.repositories.base import BaseRepository


class ChannelRepository(BaseRepository[Channel]):
    """Repository for Channel entity and related operations."""

    def __init__(self, db: Session):
        super().__init__(Channel, db)
        self.model = self.model_class

    def create(self, channel_data: dict) -> Channel:
        """Create a new channel."""
        channel = Channel(**channel_data)
        try:
            self.db.add(channel)
            self.db.commit()
            self.db.refresh(channel)
            return channel
        except IntegrityError:
            self.db.rollback()
            raise

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        channel_type: Optional[str] = None,
    ) -> List[Channel]:
        """Get all channels with optional filtering."""
        stmt = select(Channel)

        if channel_type is not None:
            stmt = stmt.filter(Channel.channel_type == channel_type)

        stmt = stmt.offset(skip).limit(limit)
        return list(self.db.scalars(stmt).all())

    def get_public_channels(
        self,
        user_permission_level: int,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Channel]:
        """Get channels visible to a user with a specific permission level."""
        visible_roles = [role for role, level in ROLE_HIERARCHY.items() if level >= user_permission_level]
        stmt = select(Channel).filter(Channel.required_role_read.in_(visible_roles)).offset(skip).limit(limit)
        return list(self.db.scalars(stmt).all())

    def update(self, channel_id: uuid.UUID, update_data: dict) -> Optional[Channel]:
        """Update a channel."""
        channel = self.get_by_id(channel_id)
        if not channel:
            return None

        for key, value in update_data.items():
            if hasattr(channel, key):
                setattr(channel, key, value)

        self.db.commit()
        self.db.refresh(channel)
        return channel

    def add_member(
        self,
        channel_id: uuid.UUID,
        user_id: uuid.UUID,
        role: ChannelRole = ChannelRole.USER,
    ) -> Optional[ChannelMember]:
        """Add a user to a channel or return existing membership."""
        channel = self.get_by_id(channel_id)
        if not channel:
            return None

        existing = self.get_member(channel_id, user_id)
        if existing:
            return existing

        membership = ChannelMember(channel_id=channel_id, user_id=user_id, role=role)
        self.db.add(membership)
        self.db.commit()
        self.db.refresh(membership)
        return membership

    def bulk_add_members(self, memberships: List[dict]) -> None:
        """
        Bulk add multiple channel members without committing.
        """
        members = [ChannelMember(**m) for m in memberships]
        self.db.bulk_save_objects(members)
        self.db.flush()

    def get_member(self, channel_id: uuid.UUID, user_id: uuid.UUID) -> Optional[ChannelMember]:
        """Get a specific member's info."""
        stmt = select(ChannelMember).filter(ChannelMember.channel_id == channel_id, ChannelMember.user_id == user_id)
        return self.db.scalar(stmt)

    def get_members(self, channel_id: uuid.UUID) -> Optional[List[ChannelMember]]:
        """Get all members of a channel."""
        channel = self.get_by_id(channel_id)
        if not channel:
            return None

        stmt = select(ChannelMember).filter(ChannelMember.channel_id == channel_id)
        return list(self.db.scalars(stmt).all())

    def update_member_role(
        self,
        channel_id: uuid.UUID,
        user_id: uuid.UUID,
        new_role: ChannelRole,
    ) -> Optional[ChannelMember]:
        """Update a member's role in a channel."""
        membership = self.get_member(channel_id, user_id)
        if not membership:
            return None

        membership.role = new_role
        self.db.commit()
        self.db.refresh(membership)
        return membership

    def remove_member(self, channel_id: uuid.UUID, user_id: uuid.UUID) -> Optional[ChannelMember]:
        """Remove a user from a channel."""
        membership = self.get_member(channel_id, user_id)
        if not membership:
            return None

        self.db.delete(membership)
        self.db.commit()
        return membership

    def ban_member(
        self,
        channel_id: uuid.UUID,
        user_id: uuid.UUID,
        motive: str,
        duration: datetime.timedelta,
        banned_by: Optional[uuid.UUID] = None,
    ) -> Optional[ChannelBan]:
        """Ban a user from a channel."""
        channel = self.get_by_id(channel_id)
        if not channel:
            return None

        membership = self.get_member(channel_id, user_id)
        if membership:
            membership.is_banned = True

        stmt = select(ChannelBan).filter(
            ChannelBan.channel_id == channel_id,
            ChannelBan.user_id == user_id,
            ChannelBan.active,
        )
        active_bans = list(self.db.scalars(stmt).all())
        for ban in active_bans:
            ban.active = False

        ban = ChannelBan(
            channel_id=channel_id,
            user_id=user_id,
            motive=motive,
            duration=duration,
            active=True,
            banned_by=banned_by,
        )
        self.db.add(ban)
        self.db.commit()
        self.db.refresh(ban)
        return ban

    def unban_member(
        self,
        channel_id: uuid.UUID,
        user_id: uuid.UUID,
        motive: str,
        unbanned_by: Optional[uuid.UUID] = None,
    ) -> Optional[ChannelUnban]:
        """Unban a member from a channel."""
        channel = self.get_by_id(channel_id)
        if not channel:
            return None

        membership = self.get_member(channel_id, user_id)
        if membership:
            membership.is_banned = False

        stmt = select(ChannelBan).filter(
            ChannelBan.channel_id == channel_id,
            ChannelBan.user_id == user_id,
            ChannelBan.active,
        )
        active_bans = list(self.db.scalars(stmt).all())
        for ban in active_bans:
            ban.active = False

        unban = ChannelUnban(
            channel_id=channel_id,
            user_id=user_id,
            motive=motive,
            unbanned_by=unbanned_by,
        )
        self.db.add(unban)
        self.db.commit()
        self.db.refresh(unban)
        return unban
