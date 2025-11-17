import uuid
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.core.logger import logger
from app.models import HousingAmenityTableModel, HousingCategoryTableModel, HousingOfferTableModel
from app.repositories.base import BaseRepository
from app.schemas import FileAssociationCreate


class HousingOfferRepository(BaseRepository[HousingOfferTableModel]):
    """Repository for HousingOffer entity."""

    def __init__(self, db: Session):
        super().__init__(HousingOfferTableModel, db)
        self.model = self.model_class

    def create(
        self,
        offer_data: dict,
        amenity_codes: Optional[List[int]] = None,
        photo_ids: Optional[List[uuid.UUID]] = None,
        file_association_service=None,
    ) -> HousingOfferTableModel:
        """Create a new housing offer with amenities and photos."""
        amenities_objs = []
        if amenity_codes:
            stmt = select(HousingAmenityTableModel).filter(HousingAmenityTableModel.code.in_(amenity_codes))
            amenities_objs = list(self.db.scalars(stmt).all())
            missing = set(amenity_codes) - {a.code for a in amenities_objs}
            if missing:
                raise ValueError(f"Amenities not found: {missing}")

        offer = HousingOfferTableModel(**offer_data, amenities=amenities_objs)

        try:
            self.db.add(offer)
            self.db.commit()
            self.db.refresh(offer)

            if photo_ids:
                if file_association_service is None:
                    from app.domains.file.file_association_service import FileAssociationService

                    file_association_service = FileAssociationService(self.db)

                associations = [
                    FileAssociationCreate(
                        file_id=file_id,
                        entity_type="housing_offer",
                        entity_id=offer.id,
                        order=index,
                        category="photo",
                    )
                    for index, file_id in enumerate(photo_ids)
                ]

                try:
                    file_association_service.create_associations_bulk(associations, current_user=None)
                    self.db.refresh(offer)
                except Exception as e:
                    logger.error(f"Warning: Failed to create photo associations: {e}")

            return offer

        except IntegrityError as e:
            self.db.rollback()
            raise ValueError(f"Database integrity error: {str(e)}")
        except Exception:
            self.db.rollback()
            raise

    def get_by_id(self, offer_id: uuid.UUID) -> Optional[HousingOfferTableModel]:
        """Get housing offer by ID with relationships loaded."""
        stmt = (
            select(HousingOfferTableModel)
            .options(
                joinedload(HousingOfferTableModel.category),
                joinedload(HousingOfferTableModel.file_associations),
                joinedload(HousingOfferTableModel.amenities),
            )
            .filter(HousingOfferTableModel.id == offer_id)
        )
        return self.db.scalar(stmt)

    def get_all(self, skip: int = 0, limit: int = 100) -> List[HousingOfferTableModel]:
        """Get all housing offers with pagination."""
        stmt = select(HousingOfferTableModel).offset(skip).limit(limit)
        return list(self.db.scalars(stmt).all())

    def get_filtered(
        self,
        city: Optional[str] = None,
        category_name: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[HousingOfferTableModel]:
        """Get filtered housing offers."""
        stmt = select(HousingOfferTableModel).options(joinedload(HousingOfferTableModel.category))

        if city:
            stmt = stmt.filter(HousingOfferTableModel.city.ilike(f"%{city}%"))
        if category_name:
            stmt = stmt.filter(
                HousingOfferTableModel.category.has(HousingCategoryTableModel.name.ilike(f"%{category_name}%"))
            )
        if min_price is not None:
            stmt = stmt.filter(HousingOfferTableModel.price >= min_price)
        if max_price is not None:
            stmt = stmt.filter(HousingOfferTableModel.price <= max_price)
        if status:
            stmt = stmt.filter(HousingOfferTableModel.status == status)

        stmt = stmt.offset(skip).limit(limit)
        return list(self.db.scalars(stmt).all())

    def get_by_user(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> List[HousingOfferTableModel]:
        """Get all housing offers by a user."""
        stmt = (
            select(HousingOfferTableModel)
            .options(joinedload(HousingOfferTableModel.file_associations))
            .filter(HousingOfferTableModel.user_id == user_id)
            .order_by(HousingOfferTableModel.posted_date.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).unique().all())

    def update(self, offer_id: uuid.UUID, update_data: dict) -> Optional[HousingOfferTableModel]:
        """Update a housing offer."""
        offer = self.get_by_id(offer_id)
        if not offer:
            return None

        for key, value in update_data.items():
            if hasattr(offer, key):
                setattr(offer, key, value)

        self.db.commit()
        self.db.refresh(offer)
        return offer

    def add_amenity(self, offer_id: uuid.UUID, amenity_code: int) -> Optional[HousingOfferTableModel]:
        """Add amenity to offer."""
        offer = self.get_by_id(offer_id)
        stmt = select(HousingAmenityTableModel).filter_by(code=amenity_code)
        amenity = self.db.scalar(stmt)

        if not offer or not amenity:
            return None

        if amenity not in offer.amenities:
            offer.amenities.append(amenity)
            self.db.commit()
            self.db.refresh(offer)

        return offer

    def remove_amenity(self, offer_id: uuid.UUID, amenity_code: int) -> Optional[HousingOfferTableModel]:
        """Remove amenity from offer."""
        offer = self.get_by_id(offer_id)
        stmt = select(HousingAmenityTableModel).filter_by(code=amenity_code)
        amenity = self.db.scalar(stmt)

        if not offer or not amenity:
            return None

        if amenity in offer.amenities:
            offer.amenities.remove(amenity)
            self.db.commit()
            self.db.refresh(offer)

        return offer
