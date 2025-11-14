import uuid
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.domains.housing.offer_repository import HousingOfferRepository
from app.schemas import (
    HousingOfferCreate,
    HousingOfferDetail,
    HousingOfferList,
    HousingOfferRead,
    HousingOfferUpdate,
)


class HousingOfferService:
    """Service layer for housing offer business logic."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = HousingOfferRepository(db)

    def create_offer(self, offer_in: HousingOfferCreate) -> HousingOfferRead:
        """Create a new housing offer."""
        try:
            photo_ids = offer_in.photo_ids
            amenity_codes = offer_in.amenities
            offer_data = offer_in.model_dump(exclude={"amenities", "photo_ids"}, exclude_none=True)

            offer = self.repository.create(offer_data, amenity_codes, photo_ids)
            return HousingOfferRead.model_validate(offer)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Offer creation failed: {e}")

    def get_offer_by_id(self, offer_id: uuid.UUID) -> HousingOfferDetail:
        """Get housing offer by ID."""
        offer = self.repository.get_by_id(offer_id)
        if not offer:
            raise HTTPException(status_code=404, detail="Offer not found.")

        offer_detail = HousingOfferDetail.model_validate(offer)
        offer_detail.photo_count = len(offer.photos)
        return offer_detail

    def list_offers(
        self,
        skip: int = 0,
        limit: int = 20,
        city: Optional[str] = None,
        category_name: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        status_filter: Optional[str] = "active",
    ) -> List[HousingOfferList]:
        """List housing offers with filters."""
        offers = self.repository.get_filtered(
            city=city,
            category_name=category_name,
            min_price=min_price,
            max_price=max_price,
            status=status_filter,
            skip=skip,
            limit=limit,
        )
        return [HousingOfferList.model_validate(o) for o in offers]

    def list_offers_by_user(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20,
    ) -> List[HousingOfferList]:
        """List all offers by a specific user."""
        offers = self.repository.get_by_user(user_id, skip, limit)
        return [
            HousingOfferList.model_validate({**o.__dict__, "base_image": o.photos[0].url if o.photos else None})
            for o in offers
        ]

    def update_offer(
        self,
        offer_id: uuid.UUID,
        offer_update: HousingOfferUpdate,
        user_id: uuid.UUID,
        is_admin: bool,
    ) -> HousingOfferRead:
        """Update housing offer."""
        offer = self.repository.get_by_id(offer_id)
        if not offer:
            raise HTTPException(status_code=404, detail="Offer not found.")

        if offer.user_id != user_id and not is_admin:
            raise HTTPException(status_code=403, detail="Not authorized to update this offer.")

        update_data = offer_update.model_dump(exclude_unset=True)
        updated_offer = self.repository.update(offer_id, update_data)

        if not updated_offer:
            raise HTTPException(status_code=400, detail="Failed to update offer.")

        return HousingOfferRead.model_validate(updated_offer)

    def delete_offer(
        self,
        offer_id: uuid.UUID,
        user_id: uuid.UUID,
        is_admin: bool,
    ) -> None:
        """Delete housing offer."""
        offer = self.repository.get_by_id(offer_id)
        if not offer:
            raise HTTPException(status_code=404, detail="Offer not found.")

        if offer.user_id != user_id and not is_admin:
            raise HTTPException(status_code=403, detail="Not authorized to delete this offer.")

        self.repository.delete(offer)

    def add_amenity(
        self,
        offer_id: uuid.UUID,
        amenity_code: int,
        user_id: uuid.UUID,
        is_admin: bool,
    ) -> HousingOfferRead:
        """Add amenity to offer."""
        offer = self.repository.get_by_id(offer_id)
        if not offer:
            raise HTTPException(status_code=404, detail="Offer not found.")

        if offer.user_id != user_id and not is_admin:
            raise HTTPException(status_code=403, detail="Not authorized to modify this offer.")

        try:
            updated_offer = self.repository.add_amenity(offer_id, amenity_code)
            if not updated_offer:
                raise HTTPException(status_code=404, detail="Amenity not found.")
            return HousingOfferRead.model_validate(updated_offer)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to add amenity: {e}")

    def remove_amenity(
        self,
        offer_id: uuid.UUID,
        amenity_code: int,
        user_id: uuid.UUID,
        is_admin: bool,
    ) -> HousingOfferRead:
        """Remove amenity from offer."""
        offer = self.repository.get_by_id(offer_id)
        if not offer:
            raise HTTPException(status_code=404, detail="Offer not found.")

        if offer.user_id != user_id and not is_admin:
            raise HTTPException(status_code=403, detail="Not authorized to modify this offer.")

        try:
            updated_offer = self.repository.remove_amenity(offer_id, amenity_code)
            if not updated_offer:
                raise HTTPException(status_code=404, detail="Amenity not found.")
            return HousingOfferRead.model_validate(updated_offer)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to remove amenity: {e}")
