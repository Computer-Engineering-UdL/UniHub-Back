import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, List

import sqlalchemy as sa
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.housing_category import HousingCategoryTableModel
    from app.models.housing_photo import HousingPhotoTableModel
    from app.models.user import User

from app.literals.housing import GenderPreferences, OfferStatus


class HousingOfferTableModel(Base):
    """
    Represents a housing offer in the system.

    Relationships:
        user: Many-to-one -> UserTableModel
        category: Many-to-one -> HousingCategoryTableModel
        photos: One-to-many -> HousingPhotoTableModel
    """

    __tablename__ = "housing_offer"

    # ----- PRIMARY KEY -----
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # ----- FOREIGN KEYS -----
    user_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        ForeignKey("user.id"),
        nullable=False
    )

    category_id: Mapped[int] = mapped_column(
        ForeignKey("housing_category.id"),
        nullable=False
    )

    # ----- REQUIRED FIELDS -----
    title: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    description: Mapped[str] = mapped_column(sa.Text, nullable=False)
    price: Mapped[float] = mapped_column(sa.Numeric, nullable=False)
    area: Mapped[float] = mapped_column(sa.Numeric, nullable=False)
    offer_valid_until: Mapped[date] = mapped_column(nullable=False)

    # ----- OPTIONAL FIELDS -----
    deposit: Mapped[float | None] = mapped_column(sa.Numeric)
    num_rooms: Mapped[int | None] = mapped_column(sa.Integer)
    num_bathrooms: Mapped[int | None] = mapped_column(sa.Integer)
    furnished: Mapped[bool] = mapped_column(sa.Boolean, default=False, nullable=False)
    utilities_included: Mapped[bool] = mapped_column(sa.Boolean, default=False, nullable=False)
    internet_included: Mapped[bool] = mapped_column(sa.Boolean, default=False, nullable=False)
    gender_preference: Mapped[GenderPreferences | None] = mapped_column(sa.String(10))
    status: Mapped[OfferStatus] = mapped_column(sa.String(20), default="active", nullable=False)

    # ----- DATES -----
    posted_date: Mapped[datetime] = mapped_column(
        sa.DateTime, default=datetime.utcnow, nullable=False
    )
    start_date: Mapped[date] = mapped_column(nullable=False)
    end_date: Mapped[date | None] = mapped_column()

    # ----- RELATIONSHIPS -----
    user: Mapped["User"] = relationship(back_populates="housing_offers")
    category: Mapped["HousingCategoryTableModel"] = relationship(back_populates="housing_offers")
    photos: Mapped[List["HousingPhotoTableModel"]] = relationship(
        back_populates="offer",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<HousingOffer(id={self.id}, title={self.title}, status={self.status})>"
