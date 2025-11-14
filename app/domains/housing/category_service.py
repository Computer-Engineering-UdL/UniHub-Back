import uuid
from typing import List

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.domains.housing.category_repository import HousingCategoryRepository
from app.schemas import (
    HousingCategoryCreate,
    HousingCategoryList,
    HousingCategoryRead,
    HousingCategoryUpdate,
)


class HousingCategoryService:
    """Service layer for housing category business logic."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = HousingCategoryRepository(db)

    def create_category(self, category_in: HousingCategoryCreate) -> HousingCategoryRead:
        """Create a new housing category."""
        category_data = category_in.model_dump()
        category = self.repository.create(category_data)
        return HousingCategoryRead.model_validate(category)

    def get_category_by_id(self, category_id: uuid.UUID) -> HousingCategoryRead:
        """Get category by ID."""
        category = self.repository.get_by_id(category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found.")
        return HousingCategoryRead.model_validate(category)

    def list_categories(self, skip: int = 0, limit: int = 100) -> List[HousingCategoryList]:
        """List all categories."""
        categories = self.repository.get_all(skip, limit)
        return [HousingCategoryList.model_validate(cat) for cat in categories]

    def update_category(self, category_id: uuid.UUID, category_update: HousingCategoryUpdate) -> HousingCategoryRead:
        """Update a category."""
        update_data = category_update.model_dump(exclude_unset=True)
        category = self.repository.update(category_id, update_data)

        if not category:
            raise HTTPException(status_code=404, detail="Category not found.")

        return HousingCategoryRead.model_validate(category)

    def delete_category(self, category_id: uuid.UUID) -> None:
        """Delete a category."""
        category = self.repository.get_by_id(category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found.")

        self.repository.delete(category)
