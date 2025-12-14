from __future__ import annotations

import datetime
import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import Base

if TYPE_CHECKING:
    from app.models.user import User


class UserPreference(Base):
    __tablename__ = "user_preference"

    id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), ForeignKey("user.id"), unique=True,
                                               nullable=False)

    email_enabled: Mapped[bool] = mapped_column(sa.Boolean, default=True, nullable=False)
    push_enabled: Mapped[bool] = mapped_column(sa.Boolean, default=True, nullable=False)
    in_app_enabled: Mapped[bool] = mapped_column(sa.Boolean, default=True, nullable=False)

    marketing_opt_in: Mapped[bool] = mapped_column(sa.Boolean, default=False, nullable=False)

    quiet_hours_start: Mapped[datetime.time | None] = mapped_column(sa.Time, nullable=True)
    quiet_hours_end: Mapped[datetime.time | None] = mapped_column(sa.Time, nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="preferences")