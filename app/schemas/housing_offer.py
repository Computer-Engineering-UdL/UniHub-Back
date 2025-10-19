from __future__ import annotations

from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import TYPE_CHECKING, List, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

if TYPE_CHECKING:
    from .housing_category import HousingCategoryRead
    from .housing_photo import HousingPhotoRead

# Type aliases
GenderPreferences = Literal["any", "male", "female"]
OfferStatus = Literal["active", "expired", "rented", "inactive"]


# Base Schema (Shared Fields)
class HousingOfferBase(BaseModel):
    """Base schema with shared fields for create/update."""

    category_id: UUID
    title: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=5000)
    price: Decimal = Field(gt=0)
    area: Decimal = Field(gt=0)
    offer_valid_until: date

    city: str = Field(min_length=1, max_length=100)
    address: str = Field(min_length=1, max_length=255)

    start_date: date
    end_date: date | None = None

    deposit: Decimal | None = Field(default=None, ge=0)
    num_rooms: int | None = Field(default=None, ge=0)
    num_bathrooms: int | None = Field(default=None, ge=0)
    furnished: bool = Field(default=False)
    utilities_included: bool = Field(default=False)
    internet_included: bool = Field(default=False)
    gender_preference: GenderPreferences | None = None
    status: OfferStatus = Field(default="active")

    @field_validator("price")
    def round_price(cls, v: Decimal) -> Decimal:
        """Round price to 2 decimal places."""
        return v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @field_validator("end_date")
    @classmethod
    def validate_dates(cls, v: date | None, info):
        """Ensure end_date is not before start_date."""
        if v and "start_date" in info.data and v < info.data["start_date"]:
            raise ValueError("end_date cannot be earlier than start_date")
        return v


# Create Schema (For POST)
class HousingOfferCreate(HousingOfferBase):
    """Schema for creating a new housing offer."""

    user_id: UUID


# Update Schema (For PATCH)
class HousingOfferUpdate(BaseModel):
    """Schema for updating a housing offer (all fields optional)."""

    title: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, min_length=1, max_length=5000)
    start_date: date | None = None
    end_date: date | None = None
    offer_valid_until: date | None = None
    price: Decimal | None = Field(None, gt=0)
    deposit: Decimal | None = Field(None, ge=0)
    area: Decimal | None = Field(None, gt=0)
    num_rooms: int | None = Field(None, ge=0)
    num_bathrooms: int | None = Field(None, ge=0)
    furnished: bool | None = None
    utilities_included: bool | None = None
    internet_included: bool | None = None
    gender_preference: GenderPreferences | None = None
    status: OfferStatus | None = None
    category_id: UUID | None = None
    city: str | None = Field(None, min_length=1, max_length=100)
    address: str | None = Field(None, min_length=1, max_length=255)

    model_config = ConfigDict(from_attributes=True)


# Read Schema (For GET single)
class HousingOfferRead(HousingOfferBase):
    """Schema for reading housing offer data."""

    id: UUID
    user_id: UUID
    posted_date: datetime
    photos: List[str] = []

    model_config = ConfigDict(from_attributes=True)


# List Schema (For paginated list)
class HousingOfferList(BaseModel):
    """Lightweight schema for list endpoints."""

    id: UUID
    title: str
    price: Decimal
    area: Decimal
    status: OfferStatus
    posted_date: datetime

    city: str

    model_config = ConfigDict(from_attributes=True)


# Detail Schema (For GET with relationships)
class HousingOfferDetail(HousingOfferRead):
    """Detailed schema with related objects."""

    category: "HousingCategoryRead"
    photos: List["HousingPhotoRead"] = []
    photo_count: int = 0

    model_config = ConfigDict(from_attributes=True)


__all__ = [
    "HousingOfferBase",
    "HousingOfferCreate",
    "HousingOfferUpdate",
    "HousingOfferRead",
    "HousingOfferList",
    "HousingOfferDetail",
]
