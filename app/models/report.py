from __future__ import annotations

import datetime
import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import Base
from app.literals.report import ReportPriority, ReportStatus

if TYPE_CHECKING:
    from app.models.user import User


class Report(Base):
    """
    Represents a user report for content moderation.
    """

    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    reported_by_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)

    reported_user_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)

    content_type: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    content_id: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    content_title: Mapped[str | None] = mapped_column(sa.String(500), nullable=True)

    reason: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(sa.Text, nullable=True)

    status: Mapped[str] = mapped_column(sa.String(50), nullable=False, default=ReportStatus.PENDING.value)
    priority: Mapped[str] = mapped_column(sa.String(50), nullable=False, default=ReportPriority.MEDIUM.value)

    created_at: Mapped[datetime.datetime] = mapped_column(
        sa.DateTime, default=lambda: datetime.datetime.now(datetime.UTC), nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        sa.DateTime,
        default=lambda: datetime.datetime.now(datetime.UTC),
        onupdate=lambda: datetime.datetime.now(datetime.UTC),
        nullable=False,
    )

    reviewed_by_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.UUID(as_uuid=True), ForeignKey("user.id"), nullable=True
    )
    reviewed_at: Mapped[datetime.datetime | None] = mapped_column(sa.DateTime, nullable=True)
    resolution: Mapped[str | None] = mapped_column(sa.Text, nullable=True)

    reported_by_user: Mapped["User"] = relationship("User", foreign_keys=[reported_by_id], lazy="joined")
    reported_user: Mapped["User"] = relationship("User", foreign_keys=[reported_user_id], lazy="joined")
    reviewed_by_user: Mapped["User"] = relationship("User", foreign_keys=[reviewed_by_id], lazy="joined")

    def __repr__(self) -> str:
        return f"<Report(id={self.id}, status={self.status}, content_type={self.content_type})>"
