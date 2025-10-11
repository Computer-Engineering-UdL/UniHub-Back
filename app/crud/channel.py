import uuid
from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Channel, ChannelBan, ChannelMember
from app.schemas import ChannelCreate, ChannelRead, ChannelUpdate, MembershipRead


class ChannelCRUD:
    """CRUD operations for Channel model."""

    # ==========================================
    # CREATE
    # ==========================================

    @staticmethod
    def create(db: Session, channel_in: ChannelCreate) -> ChannelRead:
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
            return ChannelRead.model_validate(db_channel)
        except IntegrityError as e:
            db.rollback()
            raise e

    # ==========================================
    # READ
    # ==========================================

    @staticmethod
    def get_by_id(db: Session, channel_id: uuid.UUID) -> Optional[ChannelRead]:
        """Get channel by ID.

        Args:
            db: Database session
            channel_id: Channel UUID

        Returns:
            ChannelRead schema or None if not found
        """
        db_channel = db.query(Channel).filter(Channel.id == channel_id).first()
        if db_channel is None:
            return None
        return ChannelRead.model_validate(db_channel) if db_channel else None

    @staticmethod
    def get_all(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        channel_type: Optional[str] = None,
    ) -> list[ChannelRead]:
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
        return [ChannelRead.model_validate(ch) for ch in channels]

    # ==========================================
    # UPDATE
    # ==========================================

    @staticmethod
    def update(db: Session, channel_id: uuid.UUID, channel_update: ChannelUpdate) -> Optional[ChannelRead]:
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
        return ChannelRead.model_validate(db_channel)

    # ==========================================
    # DELETE
    # ==========================================

    @staticmethod
    def delete(db: Session, channel_id: uuid.UUID) -> bool:
        """Delete a channel.

        Args:
            db: Database session
            channel_id: Channel UUID

        Returns:
            True if deleted, False if not found
        """
        db_channel = db.query(Channel).filter(Channel.id == channel_id).first()
        if not db_channel:
            return False

        db.delete(db_channel)
        db.commit()
        return True

    # ==========================================
    # MEMBER MANAGEMENT
    # ==========================================

    @staticmethod
    def add_member(
        db: Session, channel_id: uuid.UUID, user_id: uuid.UUID, role: str = "user"
    ) -> Optional[MembershipRead]:
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
            return MembershipRead.model_validate(db_channel)

        membership = ChannelMember(channel_id=channel_id, user_id=user_id, role=role)
        db.add(membership)
        db.commit()
        db.refresh(db_channel)
        return MembershipRead.model_validate(db_channel)

    @staticmethod
    def remove_member(db: Session, channel_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Remove a user from a channel.

        Args:
            db: Database session
            channel_id: Channel UUID
            user_id: User UUID

        Returns:
            True if user removed else False if it was not removed nor found
        """
        db_channel = db.query(Channel).filter(Channel.id == channel_id).first()
        if not db_channel:
            return False

        delete_count = (
            db.query(ChannelMember)
            .filter(ChannelMember.channel_id == channel_id, ChannelMember.user_id == user_id)
            .delete()
        )

        db.commit()
        db.refresh(db_channel)
        return delete_count != 0

    # ==========================================
    # BAN MANAGEMENT
    # ==========================================

    @staticmethod
    def ban_member(
        db: Session, channel_id: uuid.UUID, user_id: uuid.UUID, motive: str, banned_by: Optional[uuid.UUID] = None
    ) -> bool:
        """Ban a user from a channel.

        Args:
            db: Database session
            channel_id: Channel UUID
            user_id: User UUID to ban
            motive: Reason for ban
            banned_by: UUID of user who initiated ban

        Returns:
            True if user banned else False
        """
        db_channel = db.query(Channel).filter(Channel.id == channel_id).first()
        if not db_channel:
            return False

        # Remove from members if present
        db.query(ChannelMember).filter(
            ChannelMember.channel_id == channel_id, ChannelMember.user_id == user_id
        ).delete()

        # Add to banned
        ban = ChannelBan(channel_id=channel_id, user_id=user_id, motive=motive, banned_by=banned_by)
        db.add(ban)
        db.commit()
        db.refresh(db_channel)
        return True

    @staticmethod
    def unban_member(db: Session, channel_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Unban a member from a channel.

        Args:
            db: Database session
            channel_id: Channel UUID
            user_id: User UUID to unban

        Returns:
            True if user unbanned else False
        """
        db_channel = db.query(Channel).filter(Channel.id == channel_id).first()
        if not db_channel:
            return False

        db.query(ChannelBan).filter(ChannelBan.channel_id == channel_id, ChannelBan.user_id == user_id).delete()

        db.commit()
        db.refresh(db_channel)
        return True
