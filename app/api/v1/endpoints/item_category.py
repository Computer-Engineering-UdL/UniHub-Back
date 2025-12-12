from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.item_category import ItemCategoryTableModel
from app.schemas.item import ItemCategoryRead

router = APIRouter()


@router.get("/", response_model=List[ItemCategoryRead])
def list_categories(db: Session = Depends(get_db)):
    """List all available item categories."""
    stmt = select(ItemCategoryTableModel).order_by(ItemCategoryTableModel.name)
    return list(db.scalars(stmt).all())
