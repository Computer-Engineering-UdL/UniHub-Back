import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.crud.housing_category import HousingCategoryCRUD
from app.schemas import (
    HousingCategoryCreate,
    HousingCategoryList,
    HousingCategoryRead,
    HousingCategoryUpdate,
)

router = APIRouter(prefix="/categories", tags=["housing categories"])

@router.post("/", response_model=HousingCategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(category_in: HousingCategoryCreate, db: Session = Depends(get_db)):
    return HousingCategoryCRUD.create(db, category_in)

@router.get("/", response_model=List[HousingCategoryList])
def list_categories(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return HousingCategoryCRUD.list(db, skip=skip, limit=limit)

@router.get("/{category_id}", response_model=HousingCategoryRead)
def get_category(category_id: uuid.UUID, db: Session = Depends(get_db)):
    category = HousingCategoryCRUD.get_by_id(db, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found.")
    return category

@router.patch("/{category_id}", response_model=HousingCategoryRead)
def update_category(category_id: uuid.UUID, category_update: HousingCategoryUpdate, db: Session = Depends(get_db)):
    category = HousingCategoryCRUD.update(db, category_id, category_update)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found.")
    return category

@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: uuid.UUID, db: Session = Depends(get_db)):
    success = HousingCategoryCRUD.delete(db, category_id)
    if not success:
        raise HTTPException(status_code=404, detail="Category not found.")
