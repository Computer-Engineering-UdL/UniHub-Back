import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.types import TokenData
from app.crud.housing_offer import HousingOfferCRUD
from app.crud.user import UserCRUD
from app.literals.users import Role
from app.schemas import (
    HousingOfferCreate,
    HousingOfferDetail,
    HousingOfferList,
    HousingOfferRead,
    HousingOfferUpdate,
)

router = APIRouter()


@router.post(
    "/",
    response_model=HousingOfferRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new housing offer",
    response_description="Returns the created housing offer.",
)
def create_offer(
    offer_in: HousingOfferCreate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Create a new housing offer.

    Only logged-in users can create offers.
    """
    offer_in.user_id = current_user.id
    try:
        offer = HousingOfferCRUD.create(db, offer_in)
        return offer
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Offer creation failed: {e}")


@router.get(
    "/{offer_id}",
    response_model=HousingOfferDetail,
    status_code=status.HTTP_200_OK,
    summary="Get a housing offer by ID",
    response_description="Returns detailed information about a housing offer, including photos and category.",
)
def get_offer(
    offer_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """
    Retrieve a specific housing offer by its unique ID.

    Includes related photos and category information.
    """
    offer = HousingOfferCRUD.get_by_id(db, offer_id)
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found.")
    return offer


@router.get(
    "/",
    response_model=List[HousingOfferList],
    status_code=status.HTTP_200_OK,
    summary="List housing offers (with filters)",
    response_description="Returns a list of filtered housing offers.",
)
def list_offers(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 20,
    city: str | None = None,
    category_name: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    status: str | None = "active",
):
    """
    Retrieve housing offers with optional filters:
    - `city`: case-insensitive substring match
    - `category_name`: filter by category name
    - `min_price`, `max_price`: price range
    - `status`: offer status (e.g. active, expired)
    """
    offers = HousingOfferCRUD.get_filtered(
        db=db,
        city=city,
        category_name=category_name,
        min_price=min_price,
        max_price=max_price,
        status=status,
        skip=skip,
        limit=limit,
    )
    return offers


@router.patch(
    "/{offer_id}",
    response_model=HousingOfferRead,
    status_code=status.HTTP_200_OK,
    summary="Update a housing offer",
    response_description="Returns the updated offer after successful modification.",
)
def update_offer(
    offer_id: uuid.UUID,
    offer_update: HousingOfferUpdate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Update an existing housing offer.

    Only the offer's owner or an administrator can perform this operation.
    """
    db_offer = HousingOfferCRUD.get_by_id(db, offer_id)
    if not db_offer:
        raise HTTPException(status_code=404, detail="Offer not found.")

    is_admin = current_user.role == Role.ADMIN
    if db_offer.user_id != current_user.id and not is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to update this offer.")

    db_user = UserCRUD.get_by_id(db, current_user.id)
    updated = HousingOfferCRUD.update(db, offer_id, offer_update, db_user)
    if not updated:
        raise HTTPException(status_code=400, detail="Failed to update offer.")
    return updated


@router.delete(
    "/{offer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a housing offer",
    response_description="Removes the offer from the database if authorized.",
)
def delete_offer(
    offer_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Delete a specific housing offer.

    Only the owner of the offer or an administrator is authorized to delete it.
    """
    db_offer = HousingOfferCRUD.get_by_id(db, offer_id)
    if not db_offer:
        raise HTTPException(status_code=404, detail="Offer not found.")

    is_admin = current_user.role == Role.ADMIN
    if db_offer.user_id != current_user.id and not is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to delete this offer.")

    db_user = UserCRUD.get_by_id(db, current_user.id)
    success = HousingOfferCRUD.delete(db, offer_id, db_user)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to delete offer.")
    return None

@router.post(
    "/{offer_id}/amenities/{code}",
    response_model=HousingOfferRead,
    status_code=status.HTTP_200_OK,
    summary="Add an amenity to a housing offer",
    response_description="Returns the offer after adding the amenity.",
)
def add_amenity_to_offer(
    offer_id: uuid.UUID,
    code: int,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Add an amenity (e.g., WIFI, PARKING) to a specific housing offer.

    Only the owner of the offer or an administrator is authorized to perform this action.
    """
    db_offer = HousingOfferCRUD.get_by_id(db, offer_id)
    if not db_offer:
        raise HTTPException(status_code=404, detail="Offer not found.")

    is_admin = current_user.role == Role.ADMIN
    if db_offer.user_id != current_user.id and not is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to modify this offer.")

    try:
        offer = HousingOfferCRUD.add_amenity(db, offer_id, code)
        if not offer:
            raise HTTPException(status_code=404, detail="Amenity not found.")
        return offer
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to add amenity: {e}")


@router.delete(
    "/{offer_id}/amenities/{code}",
    response_model=HousingOfferRead,
    status_code=status.HTTP_200_OK,
    summary="Remove an amenity from a housing offer",
    response_description="Returns the offer after removing the amenity.",
)
def remove_amenity_from_offer(
    offer_id: uuid.UUID,
    code: int,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Remove an existing amenity from a specific housing offer.

    Only the offer's owner or an administrator can perform this operation.
    """
    db_offer = HousingOfferCRUD.get_by_id(db, offer_id)
    if not db_offer:
        raise HTTPException(status_code=404, detail="Offer not found.")

    is_admin = current_user.role == Role.ADMIN
    if db_offer.user_id != current_user.id and not is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to modify this offer.")

    try:
        offer = HousingOfferCRUD.remove_amenity(db, offer_id, code)
        if not offer:
            raise HTTPException(status_code=404, detail="Amenity not found.")
        return offer
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to remove amenity: {e}")

