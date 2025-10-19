import datetime
import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.channel import Channel
    from app.models.user import User


class ChannelBan(Base):
    """Separate model for banned users with ban information."""

    __tablename__ = "channel_bans"

    id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    channel_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), ForeignKey("channel.id"))
    user_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), ForeignKey("user.id"))

    motive: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    duration: Mapped[datetime.timedelta] = mapped_column(sa.Interval, nullable=False)
    active: Mapped[bool] = mapped_column(sa.Boolean, nullable=False)

    banned_at: Mapped[datetime.datetime] = mapped_column(
        sa.DateTime(timezone=True), default=datetime.datetime.now(datetime.UTC)
    )
    banned_by: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), ForeignKey("user.id"), nullable=True)

    channel: Mapped["Channel"] = relationship(back_populates="bans")
    banned_user: Mapped["User"] = relationship(foreign_keys=[user_id])
    banner: Mapped["User"] = relationship(foreign_keys=[banned_by])


class ChannelUnban(Base):
    """Separate model for unbanned users with information."""

    __tablename__ = "channel_unbans"

    id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    channel_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), ForeignKey("channel.id"))
    user_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), ForeignKey("user.id"))

    motive: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    unbanned_at: Mapped[datetime.datetime] = mapped_column(
        sa.DateTime(timezone=True), default=datetime.datetime.now(datetime.UTC)
    )
    unbanned_by: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), ForeignKey("user.id"), nullable=True)

    channel: Mapped["Channel"] = relationship(back_populates="unbans")
    unbanned_user: Mapped["User"] = relationship(foreign_keys=[user_id])
    unbanner: Mapped["User"] = relationship(foreign_keys=[unbanned_by])
