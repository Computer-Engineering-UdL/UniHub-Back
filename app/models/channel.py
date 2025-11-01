from __future__ import annotations

import datetime
import uuid
from typing import TYPE_CHECKING, List

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.literals.channels import ChannelCategory, ChannelType
from app.literals.users import Role

if TYPE_CHECKING:
    from app.models.channel_ban import ChannelBan, ChannelUnban
    from app.models.channel_member import ChannelMember
    from app.models.message import Message
    from app.models.user import User


class Channel(Base):
    """Channel model."""

    __tablename__ = "channel"

    id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(sa.String(60), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(sa.String(120))
    channel_type: Mapped[ChannelType] = mapped_column(sa.String(50), default="public")
    category: Mapped[ChannelCategory | None] = mapped_column(
        sa.Enum(ChannelCategory),
        nullable=True,
        index=True,
        default=ChannelCategory.GENERAL,
    )
    required_role_read: Mapped[Role] = mapped_column(sa.Enum(Role), default=Role.BASIC, nullable=False, index=True)
    required_role_write: Mapped[Role] = mapped_column(sa.Enum(Role), default=Role.SELLER, nullable=False, index=True)
    created_at: Mapped[datetime.datetime] = mapped_column(sa.DateTime, default=datetime.datetime.now(datetime.UTC))
    channel_logo: Mapped[str | None] = mapped_column(sa.String(2048))

    memberships: Mapped[List[ChannelMember]] = relationship(
        "ChannelMember", back_populates="channel", cascade="all, delete-orphan"
    )

    members: Mapped[List[User]] = relationship(
        "User", secondary="channel_members", back_populates="channels", viewonly=True
    )

    bans: Mapped[List[ChannelBan]] = relationship("ChannelBan", back_populates="channel", cascade="all, delete-orphan")

    unbans: Mapped[List[ChannelUnban]] = relationship(
        "ChannelUnban", back_populates="channel", cascade="all, delete-orphan"
    )

    messages: Mapped[List[Message]] = relationship("Message", back_populates="channel", cascade="all, delete-orphan")
