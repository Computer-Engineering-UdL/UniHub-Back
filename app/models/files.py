from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import Mapped, relationship

from app.core import Base

if TYPE_CHECKING:
    from app.models import User


class File(Base):
    __tablename__ = "files"

    id = Column(sa.UUID, primary_key=True, default=uuid.uuid4)
    filename = Column(sa.String(255), nullable=False)
    content_type = Column(sa.String(100), nullable=False)
    file_data = Column(sa.LargeBinary, nullable=False)
    file_size = Column(sa.Integer, nullable=False)
    uploaded_at = Column(sa.DateTime, nullable=False, default=sa.func.now())
    deleted = Column(sa.Boolean, nullable=False, default=False)
    is_public = Column(sa.Boolean, nullable=False, default=False)

    uploader_id = Column(sa.UUID, ForeignKey("user.id"), nullable=False, index=True)
    uploaded_by: Mapped[User] = relationship("User", foreign_keys=[uploader_id])
