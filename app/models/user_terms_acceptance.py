from __future__ import annotations

import datetime
import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import Base

if TYPE_CHECKING:
    from app.models.terms import TermsTableModel
    from app.models.user import User


class UserTermsAcceptanceTableModel(Base):
    """
    Links a User to a specific version of Terms they have accepted.
    """

    __tablename__ = "user_terms_acceptance"

    id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
    terms_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), ForeignKey("terms.id"), nullable=False)

    accepted_at: Mapped[datetime.datetime] = mapped_column(
        sa.DateTime, default=lambda: datetime.datetime.now(datetime.UTC), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="accepted_terms")
    terms: Mapped["TermsTableModel"] = relationship()

    @property
    def version(self) -> str:
        """Helper to get the version string directly from the related Terms object."""
        return self.terms.version if self.terms else "Unknown"

    def __repr__(self) -> str:
        return (f"<UserTermsAcceptance(user_id={self.user_id}, terms_id={self.terms_id}, "
                f"accepted_at={self.accepted_at})>")