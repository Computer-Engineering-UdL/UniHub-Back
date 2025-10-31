from __future__ import annotations

import datetime
import uuid
from typing import TYPE_CHECKING, List

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.literals.channels import ChannelType
from app.literals.users import Role

if TYPE_CHECKING:
    from app.literals.users import Role
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
    created_at: Mapped[datetime.datetime] = mapped_column(sa.DateTime, default=datetime.datetime.now(datetime.UTC))
    channel_logo: Mapped[str | None] = mapped_column(sa.String(2048))
    category: Mapped[str] = mapped_column(
        sa.String(100), nullable=False, default="General", server_default="General", index=True
    )

    memberships: Mapped[List[ChannelMember]] = relationship(
        "ChannelMember", back_populates="channel", cascade="all, delete-orphan"
    )

    members: Mapped[List[User]] = relationship(
        "User", secondary="channel_members", back_populates="channels", viewonly=True
    )

    read_min_role: Mapped[Role] = mapped_column(
        sa.Enum(Role, name="site_role_enum", native_enum=False),
        default=Role.BASIC,
        nullable=False,
        index=True,
    )

    write_min_role: Mapped[Role] = mapped_column(
        sa.Enum(Role, name="site_role_enum", native_enum=False),
        default=Role.SELLER,
        nullable=False,
        index=True,
    )

    bans: Mapped[List[ChannelBan]] = relationship("ChannelBan", back_populates="channel", cascade="all, delete-orphan")

    unbans: Mapped[List[ChannelUnban]] = relationship(
        "ChannelUnban", back_populates="channel", cascade="all, delete-orphan"
    )

    messages: Mapped[List[Message]] = relationship("Message", back_populates="channel", cascade="all, delete-orphan")
