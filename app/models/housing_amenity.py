from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, List

import sqlalchemy as sa
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import Base

if TYPE_CHECKING:
    from app.models.housing_offer import HousingOfferTableModel


class HousingAmenityTableModel(Base):
    """
    Represents an amenity that can be associated with housing offers.
    """

    __tablename__ = "housing_amenity"

    code: Mapped[int] = mapped_column(sa.Integer, primary_key=True, autoincrement = False)
    name: Mapped[str | None] = mapped_column(sa.String(120), unique=True, nullable=True)

    offers: Mapped[List["HousingOfferTableModel"]] = relationship(
        secondary="housing_offer_amenity",
        back_populates="amenities",
        viewonly=True,
    )

    def __repr__(self) -> str:
        return f"<HousingAmenity(code={self.code}, name={self.name})>"


class HousingOfferAmenity(Base):
    """
    Join table linking HousingOffer <-> HousingAmenity.
    """

    __tablename__ = "housing_offer_amenity"
    __table_args__ = (UniqueConstraint("offer_id", "amenity_code", name="uq_offer_amenity"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    offer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("housing_offer.id", ondelete="CASCADE"), nullable=False)
    amenity_code: Mapped[int] = mapped_column(ForeignKey("housing_amenity.code", ondelete="CASCADE"), nullable=False)

    offer: Mapped["HousingOfferTableModel"] = relationship(viewonly=True)
    amenity: Mapped[HousingAmenityTableModel] = relationship(viewonly=True)
