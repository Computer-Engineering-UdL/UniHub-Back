from pydantic import BaseModel, ConfigDict


class HousingAmenityBase(BaseModel):
    """Shared fields for all amenity schemas."""
    code: int


class HousingAmenityCreate(HousingAmenityBase):
    """Schema for creating a new amenity."""
    pass


class HousingAmenityRead(HousingAmenityBase):
    """Schema for reading (returning) an amenity."""

    model_config = ConfigDict(from_attributes=True)

__all__ = [
    "HousingAmenityBase",
    "HousingAmenityCreate",
    "HousingAmenityRead",
]