import datetime
import uuid
from typing import TYPE_CHECKING, List, Optional

import sqlalchemy as sa
from sqlalchemy import Column, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.housing_offer import HousingOfferTableModel
    from app.models.user import User


class Conversation(Base):
    """
    Private conversation between two users.
    Optionally linked to a housing offer.
    """

    __tablename__ = "conversation"

    id = Column(sa.UUID, primary_key=True, default=uuid.uuid4)
    user1_id = Column(sa.UUID, ForeignKey("user.id"), nullable=False, index=True)
    user2_id = Column(sa.UUID, ForeignKey("user.id"), nullable=False, index=True)
    housing_offer_id = Column(sa.UUID, ForeignKey("housing_offer.id"), nullable=True, index=True)
    created_at = Column(sa.DateTime, nullable=False, default=datetime.datetime.now)
    last_message_at = Column(sa.DateTime, nullable=True)

    user1: Mapped["User"] = relationship("User", foreign_keys=[user1_id])
    user2: Mapped["User"] = relationship("User", foreign_keys=[user2_id])
    housing_offer: Mapped[Optional["HousingOfferTableModel"]] = relationship("HousingOfferTableModel")
    messages: Mapped[List["ConversationMessage"]] = relationship(
        "ConversationMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="ConversationMessage.created_at",
    )

    __table_args__ = (UniqueConstraint("user1_id", "user2_id", "housing_offer_id", name="uq_conversation"),)


class ConversationMessage(Base):
    """
    Individual message in a private conversation.
    """

    __tablename__ = "conversation_message"

    id = Column(sa.UUID, primary_key=True, default=uuid.uuid4)
    conversation_id = Column(sa.UUID, ForeignKey("conversation.id"), nullable=False, index=True)
    sender_id = Column(sa.UUID, ForeignKey("user.id"), nullable=False, index=True)
    content = Column(sa.String(2000), nullable=False)
    created_at = Column(sa.DateTime, nullable=False, default=datetime.datetime.now)
    is_read = Column(sa.Boolean, nullable=False, default=False)

    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")
    sender: Mapped["User"] = relationship("User")
