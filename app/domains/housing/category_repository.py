import uuid
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import HousingCategoryTableModel
from app.repositories.base import BaseRepository


class HousingCategoryRepository(BaseRepository[HousingCategoryTableModel]):
    """Repository for HousingCategory entity."""

    def __init__(self, db: Session):
        super().__init__(HousingCategoryTableModel, db)
        self.model = self.model_class

    def create(self, category_data: dict) -> HousingCategoryTableModel:
        """Create a new housing category."""
        category = HousingCategoryTableModel(**category_data)
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category

    def get_all(self, skip: int = 0, limit: int = 100) -> List[HousingCategoryTableModel]:
        """Get all categories with pagination."""
        stmt = select(HousingCategoryTableModel).offset(skip).limit(limit)
        return list(self.db.scalars(stmt).all())

    def update(self, category_id: uuid.UUID, update_data: dict) -> Optional[HousingCategoryTableModel]:
        """Update a category."""
        category = self.get_by_id(category_id)
        if not category:
            return None

        for key, value in update_data.items():
            if hasattr(category, key):
                setattr(category, key, value)

        self.db.commit()
        self.db.refresh(category)
        return category
