import datetime
import uuid
from typing import TYPE_CHECKING, List

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.literals.channels import ChannelType

if TYPE_CHECKING:
    from app.models import ChannelBan, ChannelMember, ChannelUnban, Message, User


class Channel(Base):
    """Channel model."""

    __tablename__ = "channel"

    id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(sa.String(60), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(sa.String(120))
    channel_type: Mapped[ChannelType] = mapped_column(sa.String(50), default="public")
    created_at: Mapped[datetime.datetime] = mapped_column(sa.DateTime, default=datetime.datetime.now(datetime.UTC))
    channel_logo: Mapped[str | None] = mapped_column(sa.String(2048))

    memberships: Mapped[List["ChannelMember"]] = relationship(back_populates="channel", cascade="all, delete-orphan")

    members: Mapped[List["User"]] = relationship(secondary="channel_members", back_populates="channels", viewonly=True)

    bans: Mapped[List["ChannelBan"]] = relationship(back_populates="channel", cascade="all, delete-orphan")

    unbans: Mapped[List["ChannelUnban"]] = relationship(back_populates="channel", cascade="all, delete-orphan")

    messages: Mapped[List["Message"]] = relationship(back_populates="channel", cascade="all, delete-orphan")
