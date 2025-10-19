import datetime
import uuid
from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.literals.channels import ChannelRole
from app.models import Channel, ChannelBan, ChannelMember, ChannelUnban
from app.schemas import ChannelCreate, ChannelUpdate


class ChannelCRUD:
    """CRUD operations for Channel model."""

    # ==========================================
    # CREATE
    # ==========================================

    @staticmethod
    def create(db: Session, channel_in: ChannelCreate) -> Channel:
        """Create a new channel.

        Args:
            db: Database session
            channel_in: ChannelCreate schema with validated data

        Returns:
            ChannelRead schema with created channel

        Raises:
            IntegrityError: If channel name already exists
        """
        db_channel = Channel(**channel_in.model_dump())

        try:
            db.add(db_channel)
            db.commit()
            db.refresh(db_channel)
            return db_channel
        except IntegrityError as e:
            db.rollback()
            raise e

    # ==========================================
    # READ
    # ==========================================

    @staticmethod
    def get_by_id(db: Session, channel_id: uuid.UUID) -> Optional[Channel]:
        """Get channel by ID.

        Args:
            db: Database session
            channel_id: Channel UUID

        Returns:
            ChannelRead schema or None if not found
        """
        return db.query(Channel).filter(Channel.id == channel_id).one_or_none()

    @staticmethod
    def get_all(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        channel_type: Optional[str] = None,
    ) -> list[type[Channel]]:
        """Get all channels with optional filtering.

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records
            channel_type: Filter by channel type (public/private/announcement)

        Returns:
            List of ChannelRead schemas
        """
        query = db.query(Channel)

        if channel_type is not None:
            query = query.filter(Channel.channel_type == channel_type)

        channels = query.offset(skip).limit(limit).all()
        return channels

    # ==========================================
    # UPDATE
    # ==========================================

    @staticmethod
    def update(db: Session, channel_id: uuid.UUID, channel_update: ChannelUpdate) -> type[Channel] | None:
        """Update a channel.

        Args:
            db: Database session
            channel_id: Channel UUID
            channel_update: ChannelUpdate schema with new data

        Returns:
            Updated ChannelRead or None if not found
        """
        db_channel = db.query(Channel).filter(Channel.id == channel_id).first()
        if not db_channel:
            return None

        update_data = channel_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_channel, key, value)

        db.add(db_channel)
        db.commit()
        db.refresh(db_channel)
        return db_channel

    # ==========================================
    # DELETE
    # ==========================================

    @staticmethod
    def delete(db: Session, channel_id: uuid.UUID) -> type[Channel] | None:
        """Delete a channel.

        Args:
            db: Database session
            channel_id: Channel UUID

        Returns:
            True if deleted, False if not found
        """
        db_channel = db.query(Channel).filter(Channel.id == channel_id).first()
        if not db_channel:
            return None

        db.delete(db_channel)
        db.commit()
        return db_channel

    # ==========================================
    # MEMBER MANAGEMENT
    # ==========================================

    @staticmethod
    def add_member(
        db: Session, channel_id: uuid.UUID, user_id: uuid.UUID, role: str = ChannelRole.USER
    ) -> type[ChannelMember] | None:
        """Add a user to a channel.

        Args:
            db: Database session
            channel_id: Channel UUID
            user_id: User UUID
            role: Member role (user/moderator/admin)

        Returns:
            A MembershipRead or None if channel/user not found
        """
        db_channel = db.query(Channel).filter(Channel.id == channel_id).first()
        if not db_channel:
            return None

        existing = (
            db.query(ChannelMember)
            .filter(ChannelMember.channel_id == channel_id, ChannelMember.user_id == user_id)
            .first()
        )
        if existing:
            return existing

        membership = ChannelMember(channel_id=channel_id, user_id=user_id, role=role)
        db.add(membership)
        db.commit()
        db.refresh(db_channel)
        return membership

    @staticmethod
    def remove_member(db: Session, channel_id: uuid.UUID, user_id: uuid.UUID) -> type[ChannelMember] | None:
        """Remove a user from a channel.

        Args:
            db: Database session
            channel_id: Channel UUID
            user_id: User UUID

        Returns:
            ChannelMember: The removed membership, or None if not found
        """
        membership = (
            db.query(ChannelMember)
            .filter(ChannelMember.channel_id == channel_id, ChannelMember.user_id == user_id)
            .first()
        )

        if not membership:
            return None

        db.delete(membership)
        db.commit()

        return membership

    # ==========================================
    # BAN MANAGEMENT
    # ==========================================

    @staticmethod
    def ban_member(
        db: Session,
        channel_id: uuid.UUID,
        user_id: uuid.UUID,
        motive: str,
        duration: datetime.timedelta,
        banned_by: Optional[uuid.UUID] = None,
    ) -> ChannelBan | None:
        """Ban a user from a channel.

        Args:
            db: Database session
            channel_id: Channel UUID
            user_id: User UUID to ban
            motive: Reason for ban
            duration: How long the ban lasts
            banned_by: UUID of user who initiated ban

        Returns:
            ChannelBan: The created ban record, or None if channel/member not found
        """
        db_channel = db.query(Channel).filter(Channel.id == channel_id).first()
        if not db_channel:
            return None

        membership = (
            db.query(ChannelMember)
            .filter(ChannelMember.channel_id == channel_id, ChannelMember.user_id == user_id)
            .first()
        )

        if membership:
            membership.is_banned = True

        db.query(ChannelBan).filter(
            ChannelBan.channel_id == channel_id, ChannelBan.user_id == user_id, ChannelBan.active
        ).update({"active": False})

        ban = ChannelBan(
            channel_id=channel_id, user_id=user_id, motive=motive, duration=duration, active=True, banned_by=banned_by
        )
        db.add(ban)
        db.commit()
        db.refresh(ban)

        return ban

    @staticmethod
    def unban_member(
        db: Session, channel_id: uuid.UUID, user_id: uuid.UUID, motive: str, unbanned_by: Optional[uuid.UUID] = None
    ) -> ChannelUnban | None:
        """Unban a member from a channel.

        Args:
            db: Database session
            channel_id: Channel UUID
            user_id: User UUID to unban
            motive: Reason for unban
            unbanned_by: UUID of user who initiated unban

        Returns:
            ChannelUnban: The created unban record, or None if channel not found
        """
        db_channel = db.query(Channel).filter(Channel.id == channel_id).first()
        if not db_channel:
            return None

        membership = (
            db.query(ChannelMember)
            .filter(ChannelMember.channel_id == channel_id, ChannelMember.user_id == user_id)
            .first()
        )

        if membership:
            membership.is_banned = False

        db.query(ChannelBan).filter(
            ChannelBan.channel_id == channel_id, ChannelBan.user_id == user_id, ChannelBan.active
        ).update({"active": False})

        unban = ChannelUnban(channel_id=channel_id, user_id=user_id, motive=motive, unbanned_by=unbanned_by)
        db.add(unban)
        db.commit()
        db.refresh(unban)

        return unban

    @staticmethod
    def get_members(db: Session, channel_id: uuid.UUID) -> list[type[ChannelMember]] | None:
        """
        Get all users in a channel.
        Args:
            db: Database session
            channel_id: Channel UUID to get users from
        Returns:
            A list of ChannelMember objects or None if channel not found
        """
        channel_exists = db.query(Channel).filter(Channel.id == channel_id).first()
        if channel_exists is None:
            return None

        return db.query(ChannelMember).filter(ChannelMember.channel_id == channel_id).all()

    @staticmethod
    def get_member(db: Session, channel_id: uuid.UUID, user_id: uuid.UUID) -> Optional[ChannelMember]:
        """
        Get all users in a channel.
        Args:
            db: Database session
            channel_id: Channel UUID to get the user from
            user_id: User UUID to get
        Returns:
            A list of ChannelMember objects or None if channel not found
        """
        channel_exists = db.query(Channel).filter(Channel.id == channel_id).first()
        if channel_exists is None:
            return None
        return (
            db.query(ChannelMember)
            .filter(ChannelMember.channel_id == channel_id, ChannelMember.user_id == user_id)
            .one_or_none()
        )
