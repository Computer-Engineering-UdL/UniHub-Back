from typing import List

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domains.housing.amenity_repository import HousingAmenityRepository
from app.schemas.housing_amenity import (
    HousingAmenityCreate,
    HousingAmenityRead,
)


class HousingAmenityService:
    """Service layer for housing amenity business logic."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = HousingAmenityRepository(db)

    def create_amenity(self, amenity_in: HousingAmenityCreate) -> HousingAmenityRead:
        """Create a new amenity."""
        try:
            amenity_data = amenity_in.model_dump()
            amenity = self.repository.create(amenity_data)
            return HousingAmenityRead.model_validate(amenity)
        except IntegrityError as e:
            raise HTTPException(status_code=400, detail=f"Failed to create amenity: {e}")

    def get_amenity_by_code(self, code: int) -> HousingAmenityRead:
        """Get amenity by code."""
        amenity = self.repository.get_by_code(code)
        if not amenity:
            raise HTTPException(status_code=404, detail="Amenity not found.")
        return HousingAmenityRead.model_validate(amenity)

    def list_amenities(self, skip: int = 0, limit: int = 100) -> List[HousingAmenityRead]:
        """List all amenities."""
        amenities = self.repository.get_all(skip, limit)
        return [HousingAmenityRead.model_validate(a) for a in amenities]

    def delete_amenity(self, code: int) -> None:
        """Delete an amenity."""
        amenity = self.repository.get_by_code(code)
        if not amenity:
            raise HTTPException(status_code=404, detail="Amenity not found or could not be deleted.")

        self.repository.delete(amenity)
