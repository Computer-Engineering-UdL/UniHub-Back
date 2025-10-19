from __future__ import annotations

import datetime
import uuid
from typing import TYPE_CHECKING, Any, Dict, List

import sqlalchemy as sa
from sqlalchemy import Column
from sqlalchemy.orm import Mapped, relationship

from app.core.database import Base
from app.literals.users import Role

if TYPE_CHECKING:
    from app.models.channel import Channel
    from app.models.channel_member import ChannelMember
    from app.models.housing_offer import HousingOfferTableModel
    from app.models.interest import Interest, UserInterest
    from app.models.message import Message


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
    role = Column(sa.String(50), nullable=False, default=Role.BASIC)
    is_active = Column(sa.Boolean, nullable=False, default=True)
    is_verified = Column(sa.Boolean, nullable=False, default=False)
    created_at = Column(sa.DateTime, nullable=False, default=datetime.datetime.now(datetime.UTC))

    # Use string references for relationships
    channel_memberships: Mapped[List[ChannelMember]] = relationship(
        "ChannelMember", back_populates="user", cascade="all, delete-orphan"
    )

    channels: Mapped[List[Channel]] = relationship(
        "Channel", secondary="channel_members", back_populates="members", viewonly=True
    )

    messages: Mapped[List[Message]] = relationship("Message", back_populates="user")

    housing_offers: Mapped[List[HousingOfferTableModel]] = relationship("HousingOfferTableModel", back_populates="user")

    user_interest_links: Mapped[List[UserInterest]] = relationship("UserInterest", viewonly=True)

    interests: Mapped[List[Interest]] = relationship(
        "Interest", secondary="user_interest", back_populates="users", order_by="Interest.name"
    )

    @property
    def is_admin(self) -> bool:
        """Returns True if the user has admin role."""
        return self.role.lower() == "admin"


def create_payload_from_user(db_user: User) -> Dict[str, Any]:
    return {"sub": str(db_user.id), "username": db_user.username, "email": db_user.email, "role": db_user.role}
