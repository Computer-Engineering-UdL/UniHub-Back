import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Optional
from uuid import UUID

import sqlalchemy as sa
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Column
from sqlalchemy.orm import relationship

from app.core.database import Base

GenderPreferences = Literal["any", "male", "female"]
OfferStatus = Literal["active", "expired", "rented", "inactive"]


class HousingOffer(BaseModel):
    id: UUID = Field(default_factory=uuid.uuid4)
    user_id: UUID
    # category_id: UUID
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    posted_date: datetime = Field(default_factory=datetime.now)
    start_date: date
    end_date: Optional[date] = None
    offer_valid_until: date
    price: Decimal
    deposit: Optional[Decimal] = None
    area: Decimal
    num_rooms: Optional[int] = None
    num_bathrooms: Optional[int] = None
    furnished: bool = Field(default=False)
    utilities_included: bool = Field(default=False)
    internet_included: bool = Field(default=False)
    gender_preference: Optional[GenderPreferences] = None
    photo_url: Optional[str] = None
    status: OfferStatus = Field(default="active")

    model_config = ConfigDict(from_attributes=True)


class HousingOfferTableModel(Base):
    __tablename__ = "housing_offer"

    id = Column(sa.UUID, primary_key=True, default=uuid.uuid4)
    user_id = sa.Column(sa.UUID, sa.ForeignKey("user.id"), nullable=False)
    # category_id = sa.Column(sa.UUID, sa.ForeignKey("housing_category.id"), nullable=False)
    title = sa.Column(sa.String, nullable=False)
    description = sa.Column(sa.String, nullable=False)
    posted_date = sa.Column(sa.DateTime, nullable=False, default=date.today)
    start_date = sa.Column(sa.Date, nullable=False)
    end_date = sa.Column(sa.Date, nullable=True)
    offer_valid_until = sa.Column(sa.Date, nullable=False)
    price = sa.Column(sa.Numeric, nullable=False)
    deposit = sa.Column(sa.Numeric, nullable=True)
    area = sa.Column(sa.Numeric, nullable=False)
    num_rooms = sa.Column(sa.Integer, nullable=True)
    num_bathrooms = sa.Column(sa.Integer, nullable=True)
    furnished = sa.Column(sa.Boolean, nullable=False, default=False)
    utilities_included = sa.Column(sa.Boolean, nullable=False, default=False)
    internet_included = sa.Column(sa.Boolean, nullable=False, default=False)
    gender_preference = sa.Column(sa.String, nullable=True)  # any | male | female
    photo_url = sa.Column(sa.String, nullable=True)
    status = sa.Column(sa.String, nullable=False, default="active")  # active | expired | rented | inactive

    user = relationship("UserTableModel", back_populates="housing_offers")
    # category = relationship("HousingCategoryTableModel", back_populates="housing_offers")
