import datetime
import uuid

import sqlalchemy as sa
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import Base
from app.literals.channels import ChannelRole
from app.models.channel import Channel
from app.models.user import User


class ChannelMember(Base):
    """Association object for channel memberships with extra metadata."""

    __tablename__ = "channel_members"

    channel_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), ForeignKey("channel.id"), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), ForeignKey("user.id"), primary_key=True)

    role: Mapped[ChannelRole] = mapped_column(sa.String(20), default=ChannelRole.USER)
    joined_at: Mapped[datetime.datetime] = mapped_column(sa.DateTime, default=datetime.datetime.now(datetime.UTC))
    is_banned: Mapped[bool] = mapped_column(sa.Boolean, default=False, nullable=False)

    channel: Mapped["Channel"] = relationship(back_populates="memberships")
    user: Mapped["User"] = relationship(back_populates="channel_memberships")
