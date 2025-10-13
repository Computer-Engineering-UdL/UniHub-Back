import uuid
from typing import TYPE_CHECKING, List

import sqlalchemy as sa
from sqlalchemy import Column
from sqlalchemy.orm import Mapped, relationship

from app.core.database import Base
from app.literals.users import Role

if TYPE_CHECKING:
    from app.models import Channel, ChannelMember


class User(Base):
    __tablename__ = "user"

    id = Column(sa.UUID, primary_key=True, default=uuid.uuid4)
    username = Column(sa.String(20), unique=True, nullable=False, index=True)
    email = Column(sa.String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(sa.String(255), nullable=False)
    first_name = Column(sa.String(30), nullable=False)
    last_name = Column(sa.String(30), nullable=False)
    provider = Column(sa.String(50), nullable=False, default="local")
    role: Role = Column(sa.String(50), nullable=False, default="Basic")
    phone = Column(sa.String(50), nullable=True)
    university = Column(sa.String(255), nullable=True)

    channel_memberships: Mapped[List["ChannelMember"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    channels: Mapped[List["Channel"]] = relationship(
        secondary="channel_members", back_populates="members", viewonly=True
    )
    messages = relationship("Message", back_populates="user")
    housing_offers = relationship("HousingOfferTableModel", back_populates="user")
