from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.housing_amenity import HousingAmenityTableModel
from app.repositories.base import BaseRepository


class HousingAmenityRepository(BaseRepository[HousingAmenityTableModel]):
    """Repository for HousingAmenity entity."""

    def __init__(self, db: Session):
        super().__init__(HousingAmenityTableModel, db)
        self.model = self.model_class

    def create(self, amenity_data: dict) -> HousingAmenityTableModel:
        """Create a new amenity."""
        amenity = HousingAmenityTableModel(**amenity_data)
        try:
            self.db.add(amenity)
            self.db.commit()
            self.db.refresh(amenity)
            return amenity
        except IntegrityError:
            self.db.rollback()
            raise

    def get_by_code(self, code: int) -> Optional[HousingAmenityTableModel]:
        """Get amenity by code."""
        stmt = select(HousingAmenityTableModel).filter_by(code=code)
        return self.db.scalar(stmt)

    def get_all(self, skip: int = 0, limit: int = 100) -> List[HousingAmenityTableModel]:
        """Get all amenities with pagination."""
        stmt = select(HousingAmenityTableModel).offset(skip).limit(limit)
        return list(self.db.scalars(stmt).all())
