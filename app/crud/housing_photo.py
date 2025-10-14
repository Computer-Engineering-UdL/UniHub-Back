import uuid
from typing import List, Optional

from sqlalchemy.orm import Session, joinedload

from app.models import HousingPhotoTableModel
from app.schemas import HousingPhotoCreate, HousingPhotoList, HousingPhotoRead


class HousingPhotoCRUD:

    @staticmethod
    def create(db: Session, photo_in: HousingPhotoCreate) -> HousingPhotoRead:
        db_photo = HousingPhotoTableModel(**photo_in.model_dump())
        db.add(db_photo)
        db.commit()
        db.refresh(db_photo)
        return HousingPhotoRead.model_validate(db_photo)

    @staticmethod
    def get_by_id(db: Session, photo_id: uuid.UUID) -> Optional[HousingPhotoRead]:
        db_photo = db.query(HousingPhotoTableModel).options(
            joinedload(HousingPhotoTableModel.offer)
        ).filter(HousingPhotoTableModel.id == photo_id).first()
        return HousingPhotoRead.model_validate(db_photo) if db_photo else None

    @staticmethod
    def list_by_offer(db: Session, offer_id: uuid.UUID) -> List[HousingPhotoList]:
        photos = db.query(HousingPhotoTableModel).filter(
            HousingPhotoTableModel.offer_id == offer_id
        ).all()
        return [HousingPhotoList.model_validate(p) for p in photos]

    @staticmethod
    def delete(db: Session, photo_id: uuid.UUID) -> bool:
        db_photo = db.query(HousingPhotoTableModel).filter(
            HousingPhotoTableModel.id == photo_id
        ).first()
        if not db_photo:
            return False
        db.delete(db_photo)
        db.commit()
        return True
