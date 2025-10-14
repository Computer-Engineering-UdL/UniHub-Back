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

router = APIRouter(prefix="/offers", tags=["Housing Offers"])

@router.post("/", response_model=HousingOfferRead, status_code=status.HTTP_201_CREATED)
def create_offer(
    offer_in: HousingOfferCreate,
    db: Session = Depends(get_db),
    #current_user: User = Depends(get_current_user),
):
    """
    Create a new housing offer. Only logged-in users can create.
    """

    current_user = db.query(User).first()
    if not current_user:
        raise HTTPException(status_code=404, detail="No test user found")

    offer_in.user_id = current_user.id
    try:
        offer = HousingOfferCRUD.create(db, offer_in)
        return offer
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))



@router.get("/{offer_id}", response_model=HousingOfferDetail)
def get_offer(
    offer_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """
    Get a specific housing offer by its ID.
    """
    offer = HousingOfferCRUD.get_by_id(db, offer_id)
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found.")
    return offer



@router.get("/", response_model=List[HousingOfferList])
def list_offers(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """
    Get a paginated list of housing offers.
    """
    offers = HousingOfferCRUD.get_all(db, skip=skip, limit=limit)
    return offers



@router.patch("/{offer_id}", response_model=HousingOfferRead)
def update_offer(
    offer_id: uuid.UUID,
    offer_update: HousingOfferUpdate,
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_user),

):

    """
    Update an existing offer. Only owner or admin can update.
    """

    current_user = db.query(User).first()
    if not current_user:
        raise HTTPException(status_code=404, detail="No test user found")

    db_offer = HousingOfferCRUD.get_by_id(db, offer_id)
    if not db_offer:
        raise HTTPException(status_code=404, detail="Offer not found.")

    if db_offer.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to update this offer.")

    updated = HousingOfferCRUD.update(db, offer_id, offer_update)
    if not updated:
        raise HTTPException(status_code=400, detail="Failed to update offer.")
    return updated



@router.delete("/{offer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_offer(
    offer_id: uuid.UUID,
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_user),
):
    """
    Delete an offer. Only owner or admin can delete.
    """
    current_user = db.query(User).first()
    if not current_user:
        raise HTTPException(status_code=404, detail="No test user found")

    db_offer = HousingOfferCRUD.get_by_id(db, offer_id)
    if not db_offer:
        raise HTTPException(status_code=404, detail="Offer not found.")

    if db_offer.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to delete this offer.")

    success = HousingOfferCRUD.delete(db, offer_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to delete offer.")
    return None
