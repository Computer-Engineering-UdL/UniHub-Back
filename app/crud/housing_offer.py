import uuid
from typing import List, Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.crud.file_association import FileAssociationCRUD
from app.models import HousingAmenityTableModel, HousingCategoryTableModel, HousingOfferTableModel
from app.models.user import User
from app.schemas import (
    FileAssociationCreate,
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
        photo_ids = offer_in.photo_ids
        amenities_objs = []
        if offer_in.amenities:
            amenities_objs = (
                db.query(HousingAmenityTableModel).filter(HousingAmenityTableModel.code.in_(offer_in.amenities)).all()
            )
            missing = set(offer_in.amenities) - {a.code for a in amenities_objs}
            if missing:
                raise ValueError(f"Amenities not found: {missing}")

        db_offer_data = offer_in.model_dump(exclude={"amenities", "photo_ids"}, exclude_none=True)
        db_offer = HousingOfferTableModel(**db_offer_data, amenities=amenities_objs)

        try:
            db.add(db_offer)
            db.commit()
            db.refresh(db_offer)
            if photo_ids:
                associations = [
                    FileAssociationCreate(
                        file_id=file_id,
                        entity_type="housing_offer",
                        entity_id=db_offer.id,
                        order=index,
                        category="photo",
                    )
                    for index, file_id in enumerate(photo_ids)
                ]
                FileAssociationCRUD.bulk_create(db, associations)
            return db_offer
        except IntegrityError as e:
            db.rollback()
            raise e

    @staticmethod
    def get_by_id(db: Session, offer_id: uuid.UUID) -> Optional[HousingOfferDetail]:
        db_offer = (
            db.query(HousingOfferTableModel)
            .options(
                joinedload(HousingOfferTableModel.category),
                joinedload(HousingOfferTableModel.file_associations),
                joinedload(HousingOfferTableModel.amenities),
            )
            .filter(HousingOfferTableModel.id == offer_id)
            .first()
        )

        if not db_offer:
            return None

        offer_detail = HousingOfferDetail.model_validate(db_offer)
        offer_detail.photo_count = len(db_offer.photos)
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
        current_user: User,
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
        db_offer = db.query(HousingOfferTableModel).filter(HousingOfferTableModel.id == offer_id).first()
        if not db_offer:
            return None

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
        db_offer = db.query(HousingOfferTableModel).filter(HousingOfferTableModel.id == offer_id).first()
        if not db_offer:
            return False

        if db_offer.user_id != current_user.id and not current_user.is_admin:
            raise PermissionError("You are not allowed to delete this offer.")

        db.delete(db_offer)
        db.commit()
        return True

    @staticmethod
    def get_filtered(
        db: Session,
        city: Optional[str] = None,
        category_name: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[HousingOfferList]:
        """
        Retrieve housing offers with optional filters.

        Args:
            db (Session): SQLAlchemy session.
            city (Optional[str]): Filter by city (case-insensitive).
            category_name (Optional[str]): Filter by category.
            min_price (Optional[float]): Minimum price.
            max_price (Optional[float]): Maximum price.
            status (Optional[str]): Filter by offer status (e.g. 'active').
            skip (int): Pagination offset.
            limit (int): Pagination limit.
        """
        query = db.query(HousingOfferTableModel).options(joinedload(HousingOfferTableModel.category))

        if city:
            query = query.filter(HousingOfferTableModel.city.ilike(f"%{city}%"))
        if category_name:
            query = query.filter(
                HousingOfferTableModel.category.has(HousingCategoryTableModel.name.ilike(f"%{category_name}%"))
            )
        if min_price is not None:
            query = query.filter(HousingOfferTableModel.price >= min_price)
        if max_price is not None:
            query = query.filter(HousingOfferTableModel.price <= max_price)
        if status:
            query = query.filter(HousingOfferTableModel.status == status)

        offers = query.offset(skip).limit(limit).all()
        return [HousingOfferList.model_validate(o) for o in offers]

    @staticmethod
    def add_amenity(db: Session, offer_id: uuid.UUID, amenity_code: int) -> Optional[HousingOfferRead]:
        """
        Add an amenity to a housing offer.
        """
        offer = db.query(HousingOfferTableModel).filter_by(id=offer_id).first()
        amenity = db.query(HousingAmenityTableModel).filter_by(code=amenity_code).first()

        if not offer or not amenity:
            return None

        if amenity not in offer.amenities:
            offer.amenities.append(amenity)
            db.commit()
            db.refresh(offer)

        return HousingOfferRead.model_validate(offer)

    @staticmethod
    def remove_amenity(db: Session, offer_id: uuid.UUID, amenity_code: int) -> Optional[HousingOfferRead]:
        """
        Remove an amenity from a housing offer.
        """
        offer = db.query(HousingOfferTableModel).filter_by(id=offer_id).first()
        amenity = db.query(HousingAmenityTableModel).filter_by(code=amenity_code).first()

        if not offer or not amenity:
            return None

        if amenity in offer.amenities:
            offer.amenities.remove(amenity)
            db.commit()
            db.refresh(offer)

        return HousingOfferRead.model_validate(offer)

    @staticmethod
    def get_by_user(
        db: Session,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> List[HousingOfferList]:
        """
        Retrieve all housing offers created by a specific user.
        """
        query = (
            db.query(HousingOfferTableModel)
            .options(joinedload(HousingOfferTableModel.photos))
            .filter(HousingOfferTableModel.user_id == user_id)
            .order_by(HousingOfferTableModel.posted_date.desc())
            .offset(skip)
            .limit(limit)
        )

        offers = query.all()
        return [
            HousingOfferList.model_validate({
                **o.__dict__,
                "base_image": o.photos[0].url if o.photos else None
            })
            for o in offers
        ]
