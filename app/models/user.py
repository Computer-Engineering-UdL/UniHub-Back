import datetime
import uuid
from typing import TYPE_CHECKING, List

import sqlalchemy as sa
from sqlalchemy import Column
from sqlalchemy.orm import Mapped, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models import Channel, ChannelMember


class User(Base):
    __tablename__ = "user"

    id = Column(sa.UUID, primary_key=True, default=uuid.uuid4)
    username = Column(sa.String(50), unique=True, nullable=False, index=True)
    email = Column(sa.String(255), unique=True, nullable=False, index=True)
    password = Column(sa.String(255), nullable=False)
    first_name = Column(sa.String(100), nullable=False)
    last_name = Column(sa.String(100), nullable=False)
    phone = Column(sa.String(20), nullable=True)
    university = Column(sa.String(100), nullable=True)
    avatar_url = Column(sa.String(500), nullable=True)
    room_number = Column(sa.String(20), nullable=True)
    provider = Column(sa.String(50), nullable=False, default="local")
    role = Column(sa.String(50), nullable=False, default="Basic")
    is_active = Column(sa.Boolean, nullable=False, default=True)
    is_verified = Column(sa.Boolean, nullable=False, default=False)
    created_at = Column(sa.DateTime, nullable=False, default=datetime.datetime.now(datetime.UTC))

    channel_memberships: Mapped[List["ChannelMember"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    channels: Mapped[List["Channel"]] = relationship(
        secondary="channel_members", back_populates="members", viewonly=True
    )
    messages = relationship("Message", back_populates="user")
    housing_offers = relationship("HousingOfferTableModel", back_populates="user")
