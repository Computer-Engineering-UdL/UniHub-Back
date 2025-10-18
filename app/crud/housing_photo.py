import uuid
from typing import List, Optional

from sqlalchemy.orm import Session, joinedload

from app.models import HousingPhotoTableModel
from app.schemas import HousingPhotoCreate, HousingPhotoList, HousingPhotoRead


class HousingPhotoCRUD:
    """
    CRUD operations for managing housing offer photos.
    Each photo is linked to a single offer and typically contains
    a URL to an image stored on a CDN or local server.
    """

    @staticmethod
    def create(db: Session, photo_in: HousingPhotoCreate) -> HousingPhotoRead:
        """
        Create and store a new photo record for a housing offer.

        Args:
            db (Session): Active SQLAlchemy database session.
            photo_in (HousingPhotoCreate): Pydantic schema with photo data (offer_id, URL, etc.).

        Returns:
            HousingPhotoRead: The created photo record.
        """
        db_photo = HousingPhotoTableModel(**photo_in.model_dump())
        db.add(db_photo)
        db.commit()
        db.refresh(db_photo)
        return HousingPhotoRead.model_validate(db_photo)

    @staticmethod
    def get_by_id(db: Session, photo_id: uuid.UUID) -> Optional[HousingPhotoRead]:
        """
        Retrieve a photo by its unique ID, including its related offer.

        Args:
            db (Session): Database session.
            photo_id (UUID): Unique identifier of the photo.

        Returns:
            Optional[HousingPhotoRead]: The photo if found, otherwise None.
        """
        db_photo = (
            db.query(HousingPhotoTableModel)
            .options(joinedload(HousingPhotoTableModel.offer))
            .filter(HousingPhotoTableModel.id == photo_id)
            .first()
        )
        return HousingPhotoRead.model_validate(db_photo) if db_photo else None

    @staticmethod
    def list_by_offer(db: Session, offer_id: uuid.UUID) -> List[HousingPhotoList]:
        """
        List all photos belonging to a specific housing offer.

        Args:
            db (Session): Database session.
            offer_id (UUID): The ID of the housing offer to which the photos belong.

        Returns:
            List[HousingPhotoList]: List of photo metadata associated with the offer.
        """
        photos = (
            db.query(HousingPhotoTableModel)
            .filter(HousingPhotoTableModel.offer_id == offer_id)
            .order_by(HousingPhotoTableModel.uploaded_at.asc())
            .all()
        )
        return [HousingPhotoList.model_validate(p) for p in photos]

    @staticmethod
    def delete(db: Session, photo_id: uuid.UUID) -> bool:
        """
        Delete a photo by its ID.

        Args:
            db (Session): Database session.
            photo_id (UUID): The ID of the photo to delete.

        Returns:
            bool: True if the deletion was successful, False if the photo was not found.
        """
        db_photo = (
            db.query(HousingPhotoTableModel)
            .filter(HousingPhotoTableModel.id == photo_id)
            .first()
        )
        if not db_photo:
            return False

        db.delete(db_photo)
        db.commit()
        return True
