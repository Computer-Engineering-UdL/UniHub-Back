from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, List
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import Base

if TYPE_CHECKING:
    from app.models.housing_offer import HousingOfferTableModel


class HousingCategoryTableModel(Base):
    """
    Represents a housing category (e.g. apartment, room, house).
    """

    __tablename__ = "housing_category"

    # ----- PRIMARY KEY -----
    id: Mapped[UUID] = mapped_column(sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # ----- REQUIRED FIELDS -----
    name: Mapped[str] = mapped_column(sa.String(50), nullable=False, unique=True)

    # ----- RELATIONSHIPS -----
    housing_offers: Mapped[List[HousingOfferTableModel]] = relationship(back_populates="category")

    def __repr__(self) -> str:
        return f"<HousingCategory(id={self.id}, name={self.name})>"
