from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from app.schemas import HousingOfferList

# Base Schema (Shared Fields)
class HousingPhotoBase(BaseModel):
    """Base schema with shared fields for create/update."""
    url: str = Field(min_length=1, description="Full URL of the photo stored on CDN")


# Create Schema (For POST)
class HousingPhotoCreate(HousingPhotoBase):
    """Schema for creating a new housing photo."""
    offer_id: UUID


# Update Schema (For PATCH)
class HousingPhotoUpdate(BaseModel):
    """Schema for updating a housing photo. All fields optional."""
    url: str | None = Field(None, min_length=1)
    offer_id: UUID | None = None

    model_config = ConfigDict(from_attributes=True)


# Read Schema (For GET single)
class HousingPhotoRead(HousingPhotoBase):
    """Schema for reading housing photo data."""
    id: UUID
    offer_id: UUID
    uploaded_at: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(from_attributes=True)


# List Schema (For LIST/Pagination)
class HousingPhotoList(BaseModel):
    """Lightweight schema for list endpoints."""
    id: UUID
    url: str
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Detail Schema (For GET with relationships)
class HousingPhotoDetail(HousingPhotoRead):
    """Detailed schema including related housing offer info."""

    offer: HousingOfferList

    model_config = ConfigDict(from_attributes=True)
