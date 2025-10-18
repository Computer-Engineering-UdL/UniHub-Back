from typing import TYPE_CHECKING, List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from app.schemas import HousingOfferList


# Base Schema (Shared Fields)
class HousingCategoryBase(BaseModel):
    """Base schema with shared fields for create/update."""

    name: str = Field(min_length=1, max_length=50, description="Name of the housing category")


# Create Schema (For POST)
class HousingCategoryCreate(HousingCategoryBase):
    """Schema for creating a new housing category."""

    pass


# Update Schema (For PATCH)
class HousingCategoryUpdate(BaseModel):
    """Schema for updating a housing category. All fields optional."""

    name: str | None = Field(None, min_length=1, max_length=50)

    model_config = ConfigDict(from_attributes=True)


# Read Schema (For GET single)
class HousingCategoryRead(HousingCategoryBase):
    """Schema for reading a housing category."""

    id: UUID

    model_config = ConfigDict(from_attributes=True)


# List Schema (For LIST/Pagination)
class HousingCategoryList(BaseModel):
    """Lightweight schema for listing categories."""

    id: UUID
    name: str

    model_config = ConfigDict(from_attributes=True)


# Detail Schema (For GET with relationships)
class HousingCategoryDetail(HousingCategoryRead):
    """Detailed schema including related housing offers."""

    housing_offers: List["HousingOfferList"]
    offer_count: int = 0

    model_config = ConfigDict(from_attributes=True)


__all__ = [
    "HousingCategoryBase",
    "HousingCategoryCreate",
    "HousingCategoryUpdate",
    "HousingCategoryRead",
    "HousingCategoryList",
    "HousingCategoryDetail",
]
