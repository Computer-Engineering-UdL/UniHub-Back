from __future__ import annotations

import datetime
import uuid
from typing import TYPE_CHECKING, List

import sqlalchemy as sa
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import Base
from app.literals.job import JobCategory, JobType, JobWorkplace

if TYPE_CHECKING:
    from app.models.file_association import FileAssociation
    from app.models.user import User


class SavedJob(Base):
    __tablename__ = "saved_job"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id"), primary_key=True)
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("job_offer.id"), primary_key=True)
    saved_at: Mapped[datetime.datetime] = mapped_column(sa.DateTime, default=datetime.datetime.now(datetime.UTC))


class JobApplication(Base):
    __tablename__ = "job_application"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id"), primary_key=True)
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("job_offer.id"), primary_key=True)
    applied_at: Mapped[datetime.datetime] = mapped_column(sa.DateTime, default=datetime.datetime.now(datetime.UTC))
    user: Mapped["User"] = relationship()


class JobOfferTableModel(Base):
    __tablename__ = "job_offer"

    id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
    title: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    description: Mapped[str] = mapped_column(sa.Text, nullable=False)
    category: Mapped[JobCategory] = mapped_column(sa.String(50), nullable=False)
    job_type: Mapped[JobType] = mapped_column(sa.String(50), nullable=False)
    workplace_type: Mapped[JobWorkplace] = mapped_column(sa.String(50), default=JobWorkplace.ON_SITE)
    location: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    salary_min: Mapped[float | None] = mapped_column(sa.Numeric)
    salary_max: Mapped[float | None] = mapped_column(sa.Numeric)
    salary_period: Mapped[str] = mapped_column(sa.String(20), default="year")
    company_name: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    company_description: Mapped[str | None] = mapped_column(sa.Text)
    company_website: Mapped[str | None] = mapped_column(sa.String(255))
    company_employee_count: Mapped[str | None] = mapped_column(sa.String(50))

    created_at: Mapped[datetime.datetime] = mapped_column(sa.DateTime, default=datetime.datetime.now(datetime.UTC))
    is_active: Mapped[bool] = mapped_column(sa.Boolean, default=True)
    user: Mapped["User"] = relationship()
    file_associations: Mapped[List["FileAssociation"]] = relationship(
        "FileAssociation",
        primaryjoin="and_(JobOfferTableModel.id==foreign(FileAssociation.entity_id), "
        "FileAssociation.entity_type=='job_offer')",
        cascade="all, delete-orphan",
        lazy="selectin",
        viewonly=True,
    )

    applications: Mapped[List["JobApplication"]] = relationship(
        "JobApplication", backref="job_offer", cascade="all, delete-orphan"
    )

    @property
    def logo(self):
        return self.file_associations[0].file_url if self.file_associations else None
