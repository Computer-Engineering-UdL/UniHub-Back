from __future__ import annotations

import datetime
import uuid
from typing import TYPE_CHECKING, Any, Dict, List, Optional

import sqlalchemy as sa
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.literals.users import Role

if TYPE_CHECKING:
    from app.models.channel import Channel
    from app.models.channel_member import ChannelMember
    from app.models.connection import ConnectionTableModel
    from app.models.file_association import FileAssociation
    from app.models.housing_offer import HousingOfferTableModel
    from app.models.interest import Interest
    from app.models.job import JobOfferTableModel
    from app.models.message import Message
    from app.models.password_history import PasswordHistory
    from app.models.student_like import StudentLike
    from app.models.university import Faculty, University
    from app.models.user_preference import UserPreference
    from app.models.user_terms_acceptance import UserTermsAcceptanceTableModel



class User(Base):
    __tablename__ = "user"

    id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(sa.String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(sa.String(255), unique=True, nullable=False, index=True)
    password: Mapped[str] = mapped_column(sa.String(255), nullable=False)

    provider: Mapped[str] = mapped_column(sa.String(50), nullable=False, default="local")
    role: Mapped[str] = mapped_column(sa.String(50), nullable=False, default=Role.BASIC)

    is_active: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=True)
    is_verified: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=False)
    verified_at: Mapped[datetime.datetime | None] = mapped_column(sa.DateTime)
    created_at: Mapped[datetime.datetime] = mapped_column(sa.DateTime,
                                                          default=lambda: datetime.datetime.now(datetime.UTC))
    created_ip: Mapped[str | None] = mapped_column(sa.String(45))
    user_agent: Mapped[str | None] = mapped_column(sa.String(255))

    referral_code: Mapped[str] = mapped_column(sa.String(5), unique=True, nullable=False)
    referred_by_id: Mapped[uuid.UUID | None] = mapped_column(sa.UUID(as_uuid=True), ForeignKey("user.id"))

    student: Mapped[Optional["Student"]] = relationship(
        "Student", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )

    landlord: Mapped[Optional["Landlord"]] = relationship(
        "Landlord", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )

    recruiter: Mapped[Optional["Recruiter"]] = relationship(
        "Recruiter", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )

    messages: Mapped[List["Message"]] = relationship("Message", back_populates="user")

    # Files (Avatar, documents attached to user directly if any)
    file_associations: Mapped[List["FileAssociation"]] = relationship(
        "FileAssociation",
        primaryjoin="and_(User.id==foreign(FileAssociation.entity_id), "
                    "FileAssociation.entity_type=='user')",
        cascade="all, delete-orphan",
        lazy="selectin",
        viewonly=True,
    )

    accepted_terms: Mapped[List["UserTermsAcceptanceTableModel"]] = relationship(
        "UserTermsAcceptanceTableModel", back_populates="user"
    )

    connections: Mapped[List["ConnectionTableModel"]] = relationship(
        "ConnectionTableModel", back_populates="user", cascade="all, delete-orphan"
    )

    password_history: Mapped[List["PasswordHistory"]] = relationship(
        "PasswordHistory", back_populates="user", cascade="all, delete-orphan",
        order_by="PasswordHistory.created_at.desc()"
    )

    preferences: Mapped[Optional["UserPreference"]] = relationship(
        "UserPreference",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="joined"
    )

    @property
    def is_admin(self) -> bool:
        return self.role.lower() == "admin"

    @property
    def avatar(self) -> Optional["FileAssociation"]:
        for assoc in self.file_associations:
            if assoc.category == "avatar":
                return assoc
        return None


def create_payload_from_user(db_user: User) -> Dict[str, Any]:
    return {
        "sub": str(db_user.id),
        "username": db_user.username,
        "email": db_user.email,
        "role": db_user.role,
    }

class Student(Base):
    __tablename__ = "student"

    id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), ForeignKey("user.id"), unique=True,
                                               nullable=False)

    first_name: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    phone: Mapped[str | None] = mapped_column(sa.String(20))

    university_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("university.id"))
    faculty_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("faculty.id"))
    year_of_graduation: Mapped[int | None] = mapped_column(sa.Integer)

    user: Mapped["User"] = relationship("User", back_populates="student")

    faculty: Mapped["Faculty"] = relationship("Faculty")
    university: Mapped["University"] = relationship("University")

    interests: Mapped[List["Interest"]] = relationship(
        "Interest",
        secondary="student_interest",
        back_populates="students",
        order_by="Interest.name",
    )

    likes: Mapped[List["StudentLike"]] = relationship(
        "StudentLike", cascade="all, delete-orphan", back_populates="student"
    )

    channel_memberships: Mapped[List["ChannelMember"]] = relationship(
        "ChannelMember", back_populates="student", cascade="all, delete-orphan"
    )
    channels: Mapped[List["Channel"]] = relationship(
        "Channel", secondary="channel_members", back_populates="members", viewonly=True
    )
    # student identity card
    file_associations: Mapped[List["FileAssociation"]] = relationship(
        "FileAssociation",
        primaryjoin="and_(Student.id==foreign(FileAssociation.entity_id), "
                    "FileAssociation.entity_type=='student')",
        cascade="all, delete-orphan",
        lazy="selectin",
        viewonly=True,
    )

    @property
    def id_card_front(self) -> Optional["FileAssociation"]:
        for assoc in self.file_associations:
            if assoc.category == "student_id_front":
                return assoc
        return None

    @property
    def id_card_back(self) -> Optional["FileAssociation"]:
        for assoc in self.file_associations:
            if assoc.category == "student_id_back":
                return assoc
        return None


class Landlord(Base):
    __tablename__ = "landlord"

    id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), ForeignKey("user.id"), unique=True,
                                               nullable=False)

    first_name: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    phone: Mapped[str | None] = mapped_column(sa.String(20))

    is_business: Mapped[bool] = mapped_column(sa.Boolean, default=False)
    company_name: Mapped[str | None] = mapped_column(sa.String(200))


    user: Mapped["User"] = relationship("User", back_populates="landlord")

    housing_offers: Mapped[List["HousingOfferTableModel"]] = relationship(
        "HousingOfferTableModel", back_populates="landlord", cascade="all, delete-orphan"
    )

    file_associations: Mapped[List["FileAssociation"]] = relationship(
        "FileAssociation",
        primaryjoin="and_(Landlord.id==foreign(FileAssociation.entity_id), "
                    "FileAssociation.entity_type=='landlord')",
        cascade="all, delete-orphan",
        lazy="selectin",
        viewonly=True,
    )

    @property
    def identity_doc(self) -> Optional["FileAssociation"]:
        for assoc in self.file_associations:
            if assoc.category == "identity_doc":
                return assoc
        return None


class Recruiter(Base):
    __tablename__ = "recruiter"

    id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), ForeignKey("user.id"), unique=True,
                                               nullable=False)

    legal_name: Mapped[str] = mapped_column(sa.String(200), nullable=False)
    registration_number: Mapped[str] = mapped_column(sa.String(100), nullable=False)

    address_data: Mapped[dict | None] = mapped_column(sa.JSON, default=dict)

    # contact person
    first_name: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    phone: Mapped[str | None] = mapped_column(sa.String(20))
    contact_email: Mapped[str | None] = mapped_column(sa.String(255))

    user: Mapped["User"] = relationship("User", back_populates="recruiter")

    job_offers: Mapped[List["JobOfferTableModel"]] = relationship("JobOfferTableModel", back_populates="recruiter")

    # company Logo
    file_associations: Mapped[List["FileAssociation"]] = relationship(
        "FileAssociation",
        primaryjoin="and_(Recruiter.id==foreign(FileAssociation.entity_id), "
                    "FileAssociation.entity_type=='recruiter')",
        cascade="all, delete-orphan",
        lazy="selectin",
        viewonly=True,
    )

    @property
    def company_logo(self) -> Optional["FileAssociation"]:
        for assoc in self.file_associations:
            if assoc.category == "company_logo":
                return assoc
        return None
