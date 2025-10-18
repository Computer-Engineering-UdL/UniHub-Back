import uuid
from typing import List, Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.models import HousingOfferTableModel
from app.models.user import User
from app.schemas import (
    HousingOfferCreate,
    HousingOfferDetail,
    HousingOfferList,
    HousingOfferRead,
    HousingOfferUpdate,
)


class HousingOfferCRUD:
    """
    CRUD operations for managing housing offers.

    This class encapsulates logic for creating, reading, updating, and deleting housing offers.
    Each offer may include related categories and photos.
    """

    @staticmethod
    def create(db: Session, offer_in: HousingOfferCreate) -> HousingOfferRead:
        """
        Create a new housing offer.

        Args:
            db (Session): Active SQLAlchemy database session.
            offer_in (HousingOfferCreate): Pydantic model containing offer details (title, price, etc.).

        Returns:
            HousingOfferRead: The newly created offer, validated with Pydantic.
        """
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
    def get_by_id(db: Session, offer_id: uuid.UUID) -> Optional[HousingOfferDetail]:
        """
        Retrieve a specific housing offer by its ID, including related category and photos.

        Args:
            db (Session): Database session.
            offer_id (UUID): Unique identifier of the offer.

        Returns:
            Optional[HousingOfferDetail]: Detailed offer data if found, otherwise None.
        """
        db_offer = (
            db.query(HousingOfferTableModel)
            .options(
                joinedload(HousingOfferTableModel.category),  # Eager-load category
                joinedload(HousingOfferTableModel.photos),    # Eager-load photos
            )
            .filter(HousingOfferTableModel.id == offer_id)
            .first()
        )

        if not db_offer:
            return None

        # Convert SQLAlchemy model to Pydantic model
        offer_detail = HousingOfferDetail.model_validate(db_offer)
        offer_detail.photo_count = len(db_offer.photos) if db_offer.photos else 0

        return offer_detail

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[HousingOfferList]:
        """
        Retrieve a paginated list of all housing offers.

        Args:
            db (Session): Database session.
            skip (int): Number of records to skip for pagination.
            limit (int): Maximum number of offers to return.

        Returns:
            List[HousingOfferList]: A list of basic offer information.
        """
        offers = db.query(HousingOfferTableModel).offset(skip).limit(limit).all()
        return [HousingOfferList.model_validate(o) for o in offers]

    @staticmethod
    def update(
        db: Session,
        offer_id: uuid.UUID,
        offer_update: HousingOfferUpdate,
        current_user: User
    ) -> Optional[HousingOfferRead]:
        """
        Update a housing offer — only the owner or an admin is allowed to modify it.

        Args:
            db (Session): Database session.
            offer_id (UUID): ID of the offer to update.
            offer_update (HousingOfferUpdate): Fields to update.
            current_user (User): The user performing the action (used for permission checking).

        Returns:
            Optional[HousingOfferRead]: The updated offer if successful, otherwise None.

        Raises:
            PermissionError: If the user is not the owner or admin.
        """
        db_offer = (
            db.query(HousingOfferTableModel)
            .filter(HousingOfferTableModel.id == offer_id)
            .first()
        )
        if not db_offer:
            return None

        # Check permissions
        if db_offer.user_id != current_user.id and not current_user.is_admin:
            raise PermissionError("You are not allowed to modify this offer.")

        # Apply updates dynamically
        update_data = offer_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_offer, key, value)

        db.add(db_offer)
        db.commit()
        db.refresh(db_offer)
        return HousingOfferRead.model_validate(db_offer)

    @staticmethod
    def delete(db: Session, offer_id: uuid.UUID, current_user: User) -> bool:
        """
        Delete a housing offer — only the owner or admin can delete it.

        Args:
            db (Session): Database session.
            offer_id (UUID): ID of the offer to delete.
            current_user (User): The user performing the deletion.

        Returns:
            bool: True if deletion succeeded, False if offer was not found.

        Raises:
            PermissionError: If the user is not the owner or admin.
        """
        db_offer = (
            db.query(HousingOfferTableModel)
            .filter(HousingOfferTableModel.id == offer_id)
            .first()
        )
        if not db_offer:
            return False

        if db_offer.user_id != current_user.id and not current_user.is_admin:
            raise PermissionError("You are not allowed to delete this offer.")

        db.delete(db_offer)
        db.commit()
        return True
