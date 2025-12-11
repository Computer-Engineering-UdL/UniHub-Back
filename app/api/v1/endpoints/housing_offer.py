import json
import uuid
from typing import List

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.api.dependencies import require_verified_email
from app.core.database import get_db
from app.core.types import TokenData
from app.domains.housing.offer_service import HousingOfferService
from app.literals.users import Role
from app.schemas import (
    HousingOfferCreate,
    HousingOfferDetail,
    HousingOfferList,
    HousingOfferRead,
    HousingOfferUpdate,
)

router = APIRouter()


def get_housing_offer_service(db: Session = Depends(get_db)) -> HousingOfferService:
    """Dependency to inject HousingOfferService."""
    return HousingOfferService(db)


@router.post(
    "/",
    response_model=HousingOfferRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new housing offer",
    response_description="Returns the created housing offer.",
)
def create_offer(
    offer_in: HousingOfferCreate,
    service: HousingOfferService = Depends(get_housing_offer_service),
    current_user: TokenData = Depends(require_verified_email),
):
    """
    Create a new housing offer.

    Only logged-in users can create offers.
    """
    offer_in.user_id = current_user.id
    return service.create_offer(offer_in)


@router.post(
    "/with-photos",
    response_model=HousingOfferRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new housing offer with photos",
    response_description="Returns the created housing offer.",
)
async def create_offer_with_photos(
    offer_data: str = Form(...),
    photos: List[UploadFile] = File(default=[]),
    cover_photo_index: int = Form(0),
    service: HousingOfferService = Depends(get_housing_offer_service),
    current_user: TokenData = Depends(require_verified_email),
):
    """
    Create a new housing offer with photos.
    """
    offer_dict = json.loads(offer_data)
    offer_in = HousingOfferCreate(**offer_dict)
    offer_in.user_id = current_user.id

    return await service.create_offer_with_photos(
        offer_in=offer_in,
        photos=photos,
        cover_photo_index=cover_photo_index,
        current_user=current_user,
    )


@router.get(
    "/{offer_id}",
    response_model=HousingOfferDetail,
    status_code=status.HTTP_200_OK,
    summary="Get a housing offer by ID",
    response_description="Returns detailed information about a housing offer, including photos and category.",
)
def get_offer(
    offer_id: uuid.UUID,
    service: HousingOfferService = Depends(get_housing_offer_service),
):
    """
    Retrieve a specific housing offer by its unique ID.

    Includes related photos and category information.
    """
    return service.get_offer_by_id(offer_id)


@router.get(
    "/",
    response_model=List[HousingOfferList],
    status_code=status.HTTP_200_OK,
    summary="List housing offers (with filters)",
    response_description="Returns a list of filtered housing offers.",
)
def list_offers(
    service: HousingOfferService = Depends(get_housing_offer_service),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
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
    return service.list_offers(
        skip=skip,
        limit=limit,
        city=city,
        category_name=category_name,
        min_price=min_price,
        max_price=max_price,
        status_filter=status,
    )


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
    service: HousingOfferService = Depends(get_housing_offer_service),
    current_user: TokenData = Depends(require_verified_email),
):
    """
    Update an existing housing offer.

    Only the offer's owner or an administrator can perform this operation.
    """
    is_admin = current_user.role == Role.ADMIN
    return service.update_offer(offer_id, offer_update, current_user.id, is_admin)


@router.delete(
    "/{offer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a housing offer",
    response_description="Removes the offer from the database if authorized.",
)
def delete_offer(
    offer_id: uuid.UUID,
    service: HousingOfferService = Depends(get_housing_offer_service),
    current_user: TokenData = Depends(require_verified_email),
):
    """
    Delete a specific housing offer.

    Only the owner of the offer or an administrator is authorized to delete it.
    """
    is_admin = current_user.role == Role.ADMIN
    service.delete_offer(offer_id, current_user.id, is_admin)


@router.get(
    "/user/{user_id}",
    response_model=List[HousingOfferList],
    status_code=status.HTTP_200_OK,
    summary="List all offers from a specific user",
    response_description="Returns all housing offers created by the given user.",
)
def list_offers_by_user(
    user_id: uuid.UUID,
    service: HousingOfferService = Depends(get_housing_offer_service),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    """
    Retrieve all housing offers created by a specific user.
    - Accessible to admins or the user themselves.
    """
    return service.list_offers_by_user(user_id, skip, limit)


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
    service: HousingOfferService = Depends(get_housing_offer_service),
    current_user: TokenData = Depends(require_verified_email),
):
    """
    Add an amenity (e.g., WIFI, PARKING) to a specific housing offer.

    Only the owner of the offer or an administrator is authorized to perform this action.
    """
    is_admin = current_user.role == Role.ADMIN
    return service.add_amenity(offer_id, code, current_user.id, is_admin)


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
    service: HousingOfferService = Depends(get_housing_offer_service),
    current_user: TokenData = Depends(require_verified_email),
):
    """
    Remove an existing amenity from a specific housing offer.

    Only the offer's owner or an administrator can perform this operation.
    """
    is_admin = current_user.role == Role.ADMIN
    return service.remove_amenity(offer_id, code, current_user.id, is_admin)
