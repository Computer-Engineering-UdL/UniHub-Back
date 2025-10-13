import uuid
from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models import HousingOfferTableModel


class HousingPhotoTableModel(Base):
    """
    Represents a photo linked to a housing offer.
    Each photo belongs to exactly one offer.
    """

    __tablename__ = "housing_photo"

    # ----- PRIMARY KEY -----
    id: Mapped[UUID] = mapped_column(sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # ----- FOREIGN KEY -----
    offer_id: Mapped[UUID] = mapped_column(
        ForeignKey("housing_offer.id"),
        nullable=False
    )

    # ----- FIELDS -----
    url: Mapped[str] = mapped_column(sa.String(255), nullable=False)  # Full CDN URL
    uploaded_at: Mapped[datetime] = mapped_column(
        sa.DateTime,
        default=datetime.now,
        nullable=False
    )

    # ----- RELATIONSHIPS -----
    offer: Mapped["HousingOfferTableModel"] = relationship(back_populates="photos")

    def __repr__(self) -> str:
        return f"<HousingPhoto(id={self.id}, offer_id={self.offer_id})>"