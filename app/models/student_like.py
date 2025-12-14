from __future__ import annotations

import datetime
import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import Base
from app.literals.like_status import LikeStatus, LikeTargetType

if TYPE_CHECKING:
    from app.models.user import Student


class StudentLike(Base):
    """
    Association object between Student and liked entities.
    Renamed from UserLike to reflect domain logic.
    """
    __tablename__ = "student_like"

    student_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        ForeignKey("student.id", ondelete="CASCADE"),
        primary_key=True
    )

    target_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), primary_key=True)
    target_type: Mapped[LikeTargetType] = mapped_column(sa.Enum(LikeTargetType), primary_key=True)

    status: Mapped[LikeStatus] = mapped_column(
        sa.Enum(LikeStatus, name="like_status_enum"),
        default=LikeStatus.ACTIVE,
        nullable=False,
        index=True,
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        sa.DateTime,
        default=lambda: datetime.datetime.now(datetime.UTC),
        onupdate=lambda: datetime.datetime.now(datetime.UTC)
    )

    student: Mapped["Student"] = relationship(back_populates="likes")
