from __future__ import annotations

import datetime
import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import Mapped, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class PasswordHistory(Base):
    """Stores hashed previous passwords to prevent password reuse."""

    __tablename__ = "password_history"

    id = Column(sa.UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(sa.UUID, ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    password_hash = Column(sa.String(255), nullable=False)
    created_at = Column(sa.DateTime, nullable=False, default=lambda: datetime.datetime.now(datetime.UTC))

    user: Mapped["User"] = relationship("User", back_populates="password_history")
