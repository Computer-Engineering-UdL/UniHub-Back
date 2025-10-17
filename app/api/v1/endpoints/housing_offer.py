import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.crud.housing_offer import HousingOfferCRUD
from app.models import User
from app.schemas import (
    HousingOfferCreate,
    HousingOfferDetail,
    HousingOfferList,
    HousingOfferRead,
    HousingOfferUpdate,
)

router = APIRouter(
    prefix="/offers",
    tags=["housing offers"],
)


@router.post(
    "/",
    response_model=HousingOfferRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new housing offer",
    response_description="Returns the created housing offer."
)
def create_offer(
    offer_in: HousingOfferCreate,
    db: Session = Depends(get_db),
    # current_user: TokenData = Depends(get_current_user),
):
    """
    Create a new housing offer.

    Only logged-in users can create offers.
    For testing purposes, the first user from the database is used.
    """
    current_user = db.query(User).first()
    if not current_user:
        raise HTTPException(status_code=404, detail="No test user found.")

    offer_in.user_id = current_user.id
    # offer_in.user_id = current_user.id
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
    response_description="Returns detailed information about a housing offer, including photos and category."
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
    summary="List all housing offers",
    response_description="Returns a list of all available housing offers (paginated)."
)
def list_offers(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """
    Retrieve a paginated list of all available housing offers.

    Args:
        skip (int): Number of offers to skip.
        limit (int): Maximum number of offers to return (default: 20).
    """
    offers = HousingOfferCRUD.get_all(db, skip=skip, limit=limit)
    return offers


@router.patch(
    "/{offer_id}",
    response_model=HousingOfferRead,
    status_code=status.HTTP_200_OK,
    summary="Update a housing offer",
    response_description="Returns the updated offer after successful modification."
)
def update_offer(
    offer_id: uuid.UUID,
    offer_update: HousingOfferUpdate,
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_user),
):
    """
    Update an existing housing offer.

    Only the offer's owner or an administrator can perform this operation.
    """
    current_user = db.query(User).first()
    if not current_user:
        raise HTTPException(status_code=404, detail="No test user found.")

    db_offer = HousingOfferCRUD.get_by_id(db, offer_id)
    if not db_offer:
        raise HTTPException(status_code=404, detail="Offer not found.")

    if db_offer.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to update this offer.")

    updated = HousingOfferCRUD.update(db, offer_id, offer_update, current_user)
    if not updated:
        raise HTTPException(status_code=400, detail="Failed to update offer.")
    return updated


@router.delete(
    "/{offer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a housing offer",
    response_description="Removes the offer from the database if authorized."
)
def delete_offer(
    offer_id: uuid.UUID,
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_user),
):
    """
    Delete a specific housing offer.

    Only the owner of the offer or an administrator is authorized to delete it.
    """
    current_user = db.query(User).first()
    if not current_user:
        raise HTTPException(status_code=404, detail="No test user found.")

    db_offer = HousingOfferCRUD.get_by_id(db, offer_id)
    if not db_offer:
        raise HTTPException(status_code=404, detail="Offer not found.")

    if db_offer.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to delete this offer.")

    success = HousingOfferCRUD.delete(db, offer_id, current_user)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to delete offer.")
    return None
