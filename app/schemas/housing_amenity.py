from pydantic import BaseModel


class HousingAmenityBase(BaseModel):
    """Shared fields for all amenity schemas."""
    code: int


class HousingAmenityCreate(HousingAmenityBase):
    """Schema for creating a new amenity."""
    pass


class HousingAmenityRead(HousingAmenityBase):
    """Schema for reading (returning) an amenity."""

    class Config:
        from_attributes = True  # allows ORM → Pydantic conversion

__all__ = [
    "HousingAmenityBase",
    "HousingAmenityCreate",
    "HousingAmenityRead",
]