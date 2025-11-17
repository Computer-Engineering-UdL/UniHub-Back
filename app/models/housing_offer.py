from __future__ import annotations

import datetime
import uuid
from datetime import date
from typing import TYPE_CHECKING, List

import sqlalchemy as sa
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import Base
from app.literals.housing import GenderPreferences, OfferStatus

if TYPE_CHECKING:
    from app.models.file_association import FileAssociation
    from app.models.housing_amenity import HousingAmenityTableModel
    from app.models.housing_category import HousingCategoryTableModel
    from app.models.user import User


class HousingOfferTableModel(Base):
    """
    Represents a housing offer in the system.

    Relationships:
        user: Many-to-one -> UserTableModel
        category: Many-to-one -> HousingCategoryTableModel
        file_associations: One-to-many -> FileAssociation (replaces photos)
        amenities: Many-to-many -> HousingAmenityTableModel
    """

    __tablename__ = "housing_offer"

    # ----- PRIMARY KEY -----
    id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # ----- FOREIGN KEYS -----
    user_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
    category_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("housing_category.id"), nullable=False)

    # ----- REQUIRED FIELDS -----
    title: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    description: Mapped[str] = mapped_column(sa.Text, nullable=False)
    price: Mapped[float] = mapped_column(sa.Numeric, nullable=False)
    area: Mapped[float] = mapped_column(sa.Numeric, nullable=False)
    offer_valid_until: Mapped[date] = mapped_column(nullable=False)
    city: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    address: Mapped[str] = mapped_column(sa.String(255), nullable=False)

    # ----- OPTIONAL FIELDS -----
    deposit: Mapped[float | None] = mapped_column(sa.Numeric)
    num_rooms: Mapped[int | None] = mapped_column(sa.Integer)
    num_bathrooms: Mapped[int | None] = mapped_column(sa.Integer)
    gender_preference: Mapped[GenderPreferences | None] = mapped_column(sa.String(10))
    status: Mapped[OfferStatus] = mapped_column(sa.String(20), default="active", nullable=False)

    # ----- BOOLEAN FIELDS -----
    furnished: Mapped[bool] = mapped_column(sa.Boolean, default=False, nullable=False)
    utilities_included: Mapped[bool] = mapped_column(sa.Boolean, default=False, nullable=False)
    internet_included: Mapped[bool] = mapped_column(sa.Boolean, default=False, nullable=False)

    # ----- ADDITIONAL FIELDS -----
    floor: Mapped[int | None] = mapped_column(sa.Integer)
    floor_number: Mapped[int | None] = mapped_column(sa.Integer)
    distance_from_campus: Mapped[str | None] = mapped_column(sa.String(100))
    utilities_cost: Mapped[float | None] = mapped_column(sa.Numeric)
    utilities_description: Mapped[str | None] = mapped_column(sa.Text)
    contract_type: Mapped[str | None] = mapped_column(sa.String(50))
    latitude: Mapped[float | None] = mapped_column(sa.Numeric(precision=10, scale=7))
    longitude: Mapped[float | None] = mapped_column(sa.Numeric(precision=10, scale=7))

    # ----- DATES -----
    posted_date: Mapped[datetime.datetime] = mapped_column(
        sa.DateTime, default=datetime.datetime.now(datetime.UTC), nullable=False
    )
    start_date: Mapped[date] = mapped_column(nullable=False)
    end_date: Mapped[date | None] = mapped_column()

    # ----- RELATIONSHIPS -----
    user: Mapped["User"] = relationship(back_populates="housing_offers")
    category: Mapped["HousingCategoryTableModel"] = relationship(back_populates="housing_offers")

    file_associations: Mapped[List["FileAssociation"]] = relationship(
        "FileAssociation",
        primaryjoin="and_(HousingOfferTableModel.id==foreign(FileAssociation.entity_id), "
        "FileAssociation.entity_type=='housing_offer')",
        cascade="all, delete-orphan",
        lazy="selectin",
        viewonly=True,
    )

    amenities: Mapped[List["HousingAmenityTableModel"]] = relationship(
        "HousingAmenityTableModel", secondary="housing_offer_amenity", lazy="selectin", back_populates="offers"
    )

    liked_by_users: Mapped[List["User"]] = relationship(
        "User",
        secondary="user_like",
        primaryjoin="and_(HousingOfferTableModel.id==UserLike.target_id, UserLike.target_type=='housing_offer')",
        secondaryjoin="User.id==UserLike.user_id",
        viewonly=True,
        back_populates=None,
        lazy="selectin",
    )

    # ----- HELPER PROPERTIES -----
    @property
    def photos(self):
        """
        Convenience property to get photo associations.
        Filters file_associations for category='photo' or no category.
        """
        return [assoc for assoc in self.file_associations if assoc.category in ("photo", None)]

    @property
    def owner_id(self):
        """Alias for user_id for backward compatibility."""
        return self.user_id

    def __repr__(self) -> str:
        return f"<HousingOffer(id={self.id}, title={self.title}, status={self.status})>"
