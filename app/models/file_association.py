from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import Base

if TYPE_CHECKING:
    from app.models import File


class FileAssociation(Base):
    """
    Generic association table linking files to any entity type.
    Supports multiple services
    """

    __tablename__ = "file_association"

    id: Mapped[UUID] = mapped_column(sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    file_id: Mapped[UUID] = mapped_column(ForeignKey("files.id"), nullable=False)

    entity_type: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    entity_id: Mapped[UUID] = mapped_column(sa.UUID(as_uuid=True), nullable=False)

    order: Mapped[int] = mapped_column(sa.Integer, default=0, nullable=False)
    category: Mapped[str | None] = mapped_column(sa.String(50))
    file_metadata: Mapped[dict | None] = mapped_column(sa.JSON)

    created_at: Mapped[datetime] = mapped_column(sa.DateTime, default=datetime.now, nullable=False)

    file: Mapped[File] = relationship("File")

    __table_args__ = (
        Index("ix_file_association_entity", "entity_type", "entity_id"),
        Index("ix_file_association_file", "file_id"),
    )

    @property
    def url(self) -> str | None:
        """Get the URL for the associated file if it's public."""
        if self.file and self.file.is_public:
            from app.core.config import settings

            return f"{settings.API_VERSION}/files/public/{self.file.id}"
        return None

    def __repr__(self) -> str:
        return "<FileAssociation(id={}, entity_type='{}', entity_id='{}', file_id='{}')>".format(
            self.id, self.entity_type, self.entity_id, self.file_id
        )
