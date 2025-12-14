from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, List

import sqlalchemy as sa
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import Base

if TYPE_CHECKING:
    from app.models import Student


class InterestCategory(Base):
    __tablename__ = "interest_category"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(sa.String(120), unique=True, nullable=False)

    interests: Mapped[List["Interest"]] = relationship(
        back_populates="category",
        cascade="all, delete-orphan",
        order_by="Interest.name",
    )


class Interest(Base):
    __tablename__ = "interest"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(sa.String(120), unique=True, nullable=False)
    category_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("interest_category.id", ondelete="CASCADE"), nullable=False
    )

    category: Mapped[InterestCategory] = relationship(back_populates="interests")

    students: Mapped[List["Student"]] = relationship(
        "Student",
        secondary="student_interest",
        back_populates="interests"
    )


class StudentInterest(Base):
    __tablename__ = "student_interest"

    __table_args__ = (sa.UniqueConstraint("student_id", "interest_id", name="uq_student_interest"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("student.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    interest_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("interest.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    student: Mapped["Student"] = relationship(viewonly=True)
    interest: Mapped["Interest"] = relationship(viewonly=True)
