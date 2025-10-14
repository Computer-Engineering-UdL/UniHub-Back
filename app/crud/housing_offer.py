import uuid
from typing import List, Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import HousingOfferTableModel
from app.models.user import User
from app.schemas import (
    HousingOfferCreate,
    HousingOfferList,
    HousingOfferRead,
    HousingOfferUpdate,
)


class HousingOfferCRUD:
    """CRUD operations for housing offers."""

    @staticmethod
    def create(db: Session, offer_in: HousingOfferCreate) -> HousingOfferRead:
        """Create a new housing offer."""
        db_offer = HousingOfferTableModel(**offer_in.model_dump())

        try:
            db.add(db_offer)
            db.commit()
            db.refresh(db_offer)
            return HousingOfferRead.model_validate(db_offer)
        except IntegrityError as e:
            db.rollback()
            raise e

    @staticmethod
    def get_by_id(db: Session, offer_id: uuid.UUID) -> Optional[HousingOfferRead]:
        """Get a housing offer by ID."""
        db_offer = db.query(HousingOfferTableModel).filter(HousingOfferTableModel.id == offer_id).first()
        return HousingOfferRead.model_validate(db_offer) if db_offer else None

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[HousingOfferList]:
        """Get a list of all housing offers."""
        offers = db.query(HousingOfferTableModel).offset(skip).limit(limit).all()
        return [HousingOfferList.model_validate(o) for o in offers]

    @staticmethod
    def update(
        db: Session,
        offer_id: uuid.UUID,
        offer_update: HousingOfferUpdate,
        current_user: User
    ) -> Optional[HousingOfferRead]:
        """Update a housing offer (only owner or admin)."""
        db_offer = db.query(HousingOfferTableModel).filter(HousingOfferTableModel.id == offer_id).first()
        if not db_offer:
            return None

        # Only owner or admin can modify
        if db_offer.user_id != current_user.id and not current_user.is_admin:
            raise PermissionError("You are not allowed to modify this offer.")

        update_data = offer_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_offer, key, value)

        db.add(db_offer)
        db.commit()
        db.refresh(db_offer)
        return HousingOfferRead.model_validate(db_offer)

    @staticmethod
    def delete(db: Session, offer_id: uuid.UUID, current_user: User) -> bool:
        """Delete a housing offer (only owner or admin)."""
        db_offer = db.query(HousingOfferTableModel).filter(HousingOfferTableModel.id == offer_id).first()
        if not db_offer:
            return False

        if db_offer.user_id != current_user.id and not current_user.is_admin:
            raise PermissionError("You are not allowed to delete this offer.")

        db.delete(db_offer)
        db.commit()
        return True