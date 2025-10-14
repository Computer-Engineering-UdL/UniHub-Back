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

    @staticmethod
    def create(db: Session, category_in: HousingCategoryCreate) -> HousingCategoryRead:
        db_category = HousingCategoryTableModel(**category_in.model_dump())
        db.add(db_category)
        db.commit()
        db.refresh(db_category)
        return HousingCategoryRead.model_validate(db_category)

    @staticmethod
    def get_by_id(db: Session, category_id: uuid.UUID) -> Optional[HousingCategoryRead]:
        db_category = db.query(HousingCategoryTableModel).filter(
            HousingCategoryTableModel.id == category_id
        ).first()
        return HousingCategoryRead.model_validate(db_category) if db_category else None

    @staticmethod
    def list(db: Session, skip: int = 0, limit: int = 100) -> List[HousingCategoryList]:
        categories = db.query(HousingCategoryTableModel).offset(skip).limit(limit).all()
        return [HousingCategoryList.model_validate(cat) for cat in categories]

    @staticmethod
    def update(db: Session, category_id: uuid.UUID, category_update: HousingCategoryUpdate) \
            -> Optional[HousingCategoryRead]:
        db_category = db.query(HousingCategoryTableModel).filter(
            HousingCategoryTableModel.id == category_id
        ).first()
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
        db_category = db.query(HousingCategoryTableModel).filter(
            HousingCategoryTableModel.id == category_id
        ).first()
        if not db_category:
            return False

        db.delete(db_category)
        db.commit()
        return True
