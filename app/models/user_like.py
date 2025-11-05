from __future__ import annotations

import datetime
import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import Base

if TYPE_CHECKING:
    from app.models import User


class UserLike(Base):
    """
    Association table connecting users with liked entities (currently housing offers).
    Can be extended in the future by using target_type.
    """
    __tablename__ = "user_like"
    __table_args__ = (
        sa.UniqueConstraint("user_id", "target_id", "target_type", name="uq_user_like"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    target_type: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    liked_at: Mapped[datetime.datetime] = mapped_column(
        sa.DateTime, default=datetime.datetime.now(datetime.UTC), nullable=False
    )

    # Optional: explicit relationships for ORM clarity
    user: Mapped["User"] = relationship(back_populates="likes", viewonly=True)
