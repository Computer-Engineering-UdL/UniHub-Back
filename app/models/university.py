from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, List

import sqlalchemy as sa
from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import Mapped, relationship

from app.core import Base

if TYPE_CHECKING:
    from app.models.user import User


class University(Base):
    __tablename__ = "university"

    id = Column(sa.UUID, primary_key=True, default=uuid.uuid4)
    name = Column(sa.String(150), unique=True, nullable=False)
    faculties: Mapped[List["Faculty"]] = relationship("Faculty", back_populates="university")


class Faculty(Base):
    __tablename__ = "faculty"

    id = Column(sa.UUID, primary_key=True, default=uuid.uuid4)
    name = Column(sa.String(150), nullable=False)
    address = Column(sa.String(255), nullable=True)
    university_id = Column(sa.UUID, ForeignKey("university.id"), nullable=False)
    university: Mapped["University"] = relationship("University", back_populates="faculties")

    users: Mapped[List["User"]] = relationship("User", back_populates="faculty")
