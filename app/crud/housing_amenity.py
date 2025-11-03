from typing import List, Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.housing_amenity import HousingAmenityTableModel
from app.schemas.housing_amenity import (
    HousingAmenityCreate,
    HousingAmenityRead,
)


class HousingAmenityCRUD:
    """
    CRUD operations for managing housing amenities.

    Keeps consistent style with HousingOfferCRUD.
    """

    @staticmethod
    def create(db: Session, amenity_in: HousingAmenityCreate) -> HousingAmenityRead:
        """
        Create a new amenity.
        """
        db_amenity = HousingAmenityTableModel(**amenity_in.model_dump())

        try:
            db.add(db_amenity)
            db.commit()
            db.refresh(db_amenity)
            return HousingAmenityRead.model_validate(db_amenity)
        except IntegrityError as e:
            db.rollback()
            raise e

    @staticmethod
    def get_by_code(db: Session, code: int) -> Optional[HousingAmenityRead]:
        """
        Retrieve an amenity by its code.
        """
        db_amenity = db.query(HousingAmenityTableModel).filter_by(code=code).first()
        if not db_amenity:
            return None
        return HousingAmenityRead.model_validate(db_amenity)

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[HousingAmenityRead]:
        """
        Retrieve all amenities with pagination.
        """
        amenities = db.query(HousingAmenityTableModel).offset(skip).limit(limit).all()
        return [HousingAmenityRead.model_validate(a) for a in amenities]

    @staticmethod
    def delete(db: Session, code: int) -> bool:
        """
        Delete an amenity by its code.
        """
        db_amenity = db.query(HousingAmenityTableModel).filter_by(code=code).first()
        if not db_amenity:
            return False

        db.delete(db_amenity)
        db.commit()
        return True
