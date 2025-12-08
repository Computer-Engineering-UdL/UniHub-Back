from __future__ import annotations

import datetime
import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.core import Base

if TYPE_CHECKING:
    pass


class TermsTableModel(Base):
    """
    Represents a version of Terms and Conditions (T&C).
    """

    __tablename__ = "terms"
    id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    version: Mapped[str] = mapped_column(sa.String(20), unique=True, nullable=False)
    content: Mapped[str] = mapped_column(sa.Text, nullable=False)

    created_at: Mapped[datetime.datetime] = mapped_column(
        sa.DateTime, default=lambda: datetime.datetime.now(datetime.UTC), nullable=False
    )

    def __repr__(self) -> str:
        return f"<Terms(id={self.id}, version={self.version}, created_at={self.created_at})>"