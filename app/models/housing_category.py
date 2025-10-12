from typing import List

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models import HousingOfferTableModel


class HousingCategoryTableModel(Base):
    """
        Represents a housing category (e.g. apartment, room, house).
        """

    __tablename__ = "housing_category"

    # ----- PRIMARY KEY -----
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # ----- REQUIRED FIELDS -----
    name: Mapped[str] = mapped_column(sa.String(50), nullable=False, unique=True)

    # ----- RELATIONSHIPS -----
    housing_offers: Mapped[List["HousingOfferTableModel"]] = relationship(
        back_populates="category"
    )

    def __repr__(self) -> str:
        return f"<HousingCategory(id={self.id}, name={self.name})>"
