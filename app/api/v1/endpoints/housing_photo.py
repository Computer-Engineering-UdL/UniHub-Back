import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.crud.housing_photo import HousingPhotoCRUD
from app.schemas import HousingPhotoCreate, HousingPhotoList, HousingPhotoRead

router = APIRouter(prefix="/photos", tags=["housing photos"])

@router.post("/", response_model=HousingPhotoRead, status_code=status.HTTP_201_CREATED)
def create_photo(photo_in: HousingPhotoCreate, db: Session = Depends(get_db)):
    return HousingPhotoCRUD.create(db, photo_in)

@router.get("/offer/{offer_id}", response_model=List[HousingPhotoList])
def list_photos_by_offer(offer_id: uuid.UUID, db: Session = Depends(get_db)):
    return HousingPhotoCRUD.list_by_offer(db, offer_id)

@router.get("/{photo_id}", response_model=HousingPhotoRead)
def get_photo(photo_id: uuid.UUID, db: Session = Depends(get_db)):
    photo = HousingPhotoCRUD.get_by_id(db, photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    return photo

@router.delete("/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_photo(photo_id: uuid.UUID, db: Session = Depends(get_db)):
    success = HousingPhotoCRUD.delete(db, photo_id)
    if not success:
        raise HTTPException(status_code=404, detail="Photo not found")
