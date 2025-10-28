import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models import HousingCategoryTableModel
from app.schemas import (
    HousingCategoryCreate,
    HousingCategoryList,
    HousingCategoryRead,
    HousingCategoryUpdate,
)


class HousingCategoryCRUD:
    """
    CRUD operations for the HousingCategory model.
    This class provides methods to create, read, update, and delete
    housing categories (e.g. flat, room, house).
    """

    @staticmethod
    def create(db: Session, category_in: HousingCategoryCreate) -> HousingCategoryRead:
        """
        Create a new housing category.

        Args:
            db (Session): Database session.
            category_in (HousingCategoryCreate): Pydantic schema containing the category data.

        Returns:
            HousingCategoryRead: The created category object.
        """
        db_category = HousingCategoryTableModel(**category_in.model_dump())
        db.add(db_category)
        db.commit()
        db.refresh(db_category)
        return HousingCategoryRead.model_validate(db_category)

    @staticmethod
    def get_by_id(db: Session, category_id: uuid.UUID) -> Optional[HousingCategoryRead]:
        """
        Retrieve a housing category by its unique ID.

        Args:
            db (Session): Database session.
            category_id (UUID): Unique identifier of the category.

        Returns:
            Optional[HousingCategoryRead]: The found category, or None if not found.
        """
        db_category = db.query(HousingCategoryTableModel).filter(HousingCategoryTableModel.id == category_id).first()
        return HousingCategoryRead.model_validate(db_category) if db_category else None

    @staticmethod
    def list(db: Session, skip: int = 0, limit: int = 100) -> List[HousingCategoryList]:
        """
        Retrieve a list of housing categories (paginated).

        Args:
            db (Session): Database session.
            skip (int): Number of records to skip (for pagination). Default is 0.
            limit (int): Maximum number of records to return. Default is 100.

        Returns:
            List[HousingCategoryList]: List of categories.
        """
        categories = db.query(HousingCategoryTableModel).offset(skip).limit(limit).all()
        return [HousingCategoryList.model_validate(cat) for cat in categories]

    @staticmethod
    def update(
        db: Session, category_id: uuid.UUID, category_update: HousingCategoryUpdate
    ) -> Optional[HousingCategoryRead]:
        """
        Update an existing housing category.

        Args:
            db (Session): Database session.
            category_id (UUID): ID of the category to update.
            category_update (HousingCategoryUpdate): Fields to update.

        Returns:
            Optional[HousingCategoryRead]: Updated category object, or None if not found.
        """
        db_category = db.query(HousingCategoryTableModel).filter(HousingCategoryTableModel.id == category_id).first()

        if not db_category:
            return None

        update_data = category_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_category, key, value)

        db.add(db_category)
        db.commit()
        db.refresh(db_category)
        return HousingCategoryRead.model_validate(db_category)

    @staticmethod
    def delete(db: Session, category_id: uuid.UUID) -> bool:
        """
        Delete a housing category by its ID.

        Args:
            db (Session): Database session.
            category_id (UUID): ID of the category to delete.

        Returns:
            bool: True if deletion was successful, False if category not found.
        """
        db_category = db.query(HousingCategoryTableModel).filter(HousingCategoryTableModel.id == category_id).first()

        if not db_category:
            return False

        db.delete(db_category)
        db.commit()
        return True
