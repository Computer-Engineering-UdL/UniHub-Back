from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import TYPE_CHECKING, Any, List, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator, model_validator

if TYPE_CHECKING:
    from .file_association import FileAssociationWithFile
    from .housing_amenity import HousingAmenityRead
    from .housing_category import HousingCategoryRead

# Type aliases
GenderPreferences = Literal["any", "male", "female"]
OfferStatus = Literal["active", "expired", "rented", "inactive"]


# Base Schema (Shared Fields)
class HousingOfferBase(BaseModel):
    """Base schema with shared fields for create/update."""

    category_id: uuid.UUID
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
    amenities: list[int] | None = Field(default=None, description="Optional list of amenity codes")
    photo_ids: list[UUID] = []


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
    gender_preference: GenderPreferences | None = None
    status: OfferStatus | None = None
    category_id: UUID | None = None
    city: str | None = Field(None, min_length=1, max_length=100)
    address: str | None = Field(None, min_length=1, max_length=255)

    amenities: list[int] | None = Field(default=None, description="Optional list of amenity codes to update")

    model_config = ConfigDict(from_attributes=True)


# Read Schema (For GET single)
class HousingOfferRead(HousingOfferBase):
    """Schema for reading housing offer data."""

    id: UUID
    user_id: UUID
    posted_date: datetime
    photo_count: int = 0

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
    user_id: UUID

    city: str
    base_image: str | None = None  # First photo URL if available

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def extract_base_image(cls, data: Any) -> Any:
        """Extract the first photo URL from the ORM model."""
        if hasattr(data, "photos") and data.photos:
            if hasattr(data, "__dict__"):
                data_dict = {**data.__dict__}
            else:
                data_dict = data

            data_dict["base_image"] = data.photos[0].url if data.photos else None
            return data_dict

        return data


# Detail Schema (For GET with relationships)
class HousingOfferDetail(HousingOfferRead):
    """Detailed schema with related objects."""

    category: "HousingCategoryRead"
    amenities: List["HousingAmenityRead"] = []
    file_associations: list[FileAssociationWithFile] = []

    @computed_field
    @property
    def photos(self) -> list[FileAssociationWithFile]:
        """Filter file_associations for photos only."""
        return [assoc for assoc in self.file_associations if assoc.category in ("photo", None)]


__all__ = [
    "HousingOfferBase",
    "HousingOfferCreate",
    "HousingOfferUpdate",
    "HousingOfferRead",
    "HousingOfferList",
    "HousingOfferDetail",
]
