from datetime import datetime

import sqlalchemy as sa
from pydantic import BaseModel, Field
from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class HousingPhoto(BaseModel):
    """
    Pydantic model representing a housing photo.

    Attributes:
        id: Optional unique identifier of the photo.
        listing_id: ID of the housing offer this photo belongs to.
        url: Full URL of the photo stored on CDN.
        uploaded_at: Timestamp when the photo was uploaded.
    """
    id: int | None = None
    listing_id: int
    url: str
    uploaded_at: datetime = Field(default_factory=datetime.now)

    class Config:
        from_attributes = True

class HousingPhotoTableModel(Base):
    """
    SQLAlchemy model representing the housing_photo table in the database.

    Relationships:
        offer: Many-to-one relationship to HousingOfferTableModel.
                Each photo belongs to exactly one housing offer.
    """
    __tablename__ = "housing_photo"

    id = Column(sa.Integer, primary_key=True, autoincrement=True)
    listing_id = Column(sa.Integer, ForeignKey("housing_offer.id"), nullable=False)
    url = Column(sa.String, nullable=False)  # full URL on CDN
    uploaded_at = Column(sa.DateTime, nullable=False, default=datetime.now)

    offer = relationship("HousingOfferTableModel", back_populates="photos")