import datetime
import uuid

import sqlalchemy as sa
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models import Channel, User


class ChannelBan(Base):
    """Separate model for banned users with ban information."""

    __tablename__ = "channel_bans"

    channel_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), ForeignKey("channel.id"), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), ForeignKey("user.id"), primary_key=True)

    motive: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    banned_at: Mapped[datetime.datetime] = mapped_column(sa.DateTime, default=datetime.datetime.now(datetime.UTC))
    banned_by: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), ForeignKey("user.id"), nullable=True)

    channel: Mapped["Channel"] = relationship(back_populates="bans")
    user: Mapped["User"] = relationship(foreign_keys=[user_id])
    banner: Mapped["User"] = relationship(foreign_keys=[banned_by])


class ChannelUnban(Base):
    """Separate model for unbanned users with information."""

    __tablename__ = "channel_unbans"

    channel_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), ForeignKey("channel.id"), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), ForeignKey("user.id"), primary_key=True)

    motive: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    unbanned_at: Mapped[datetime.datetime] = mapped_column(sa.DateTime, default=datetime.datetime.now(datetime.UTC))
    unbanned_by: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), ForeignKey("user.id"), nullable=True)

    channel: Mapped["Channel"] = relationship(back_populates="unbans")
    user: Mapped["User"] = relationship(foreign_keys=[user_id])
    unban_user: Mapped["User"] = relationship(foreign_keys=[unbanned_by])
