from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.types import TokenData
from app.domains.housing.amenity_service import HousingAmenityService
from app.literals.users import Role
from app.schemas import (
    HousingAmenityCreate,
    HousingAmenityRead,
)

router = APIRouter()


def get_amenity_service(db: Session = Depends(get_db)) -> HousingAmenityService:
    """Dependency to inject HousingAmenityService."""
    return HousingAmenityService(db)


@router.post(
    "/",
    response_model=HousingAmenityRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new amenity",
    response_description="Returns the created amenity.",
)
def create_amenity(
    amenity_in: HousingAmenityCreate,
    service: HousingAmenityService = Depends(get_amenity_service),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Create a new housing amenity definition.

    **Permissions:** Admins only.
    Used to register new amenities (e.g., WIFI, PARKING, BALCONY) in the system.
    """
    if current_user.role != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to create amenities.")

    return service.create_amenity(amenity_in)


@router.get(
    "/{code}",
    response_model=HousingAmenityRead,
    status_code=status.HTTP_200_OK,
    summary="Get an amenity by code",
    response_description="Returns a single amenity if found.",
)
def get_amenity(
    code: int,
    service: HousingAmenityService = Depends(get_amenity_service),
):
    """
    Retrieve a housing amenity by its numeric OTA code.
    """
    return service.get_amenity_by_code(code)


@router.get(
    "/",
    response_model=List[HousingAmenityRead],
    status_code=status.HTTP_200_OK,
    summary="List all amenities",
    response_description="Returns all defined housing amenities.",
)
def list_amenities(
    service: HousingAmenityService = Depends(get_amenity_service),
    skip: int = 0,
    limit: int = 100,
):
    """
    Retrieve all registered amenities with optional pagination.
    """
    return service.list_amenities(skip, limit)


@router.delete(
    "/{code}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an amenity",
    response_description="Removes an amenity from the database.",
)
def delete_amenity(
    code: int,
    service: HousingAmenityService = Depends(get_amenity_service),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Delete an existing amenity.

    **Permissions:** Admins only.
    Used when an amenity is deprecated or added by mistake.
    """
    if current_user.role != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to delete amenities.")

    service.delete_amenity(code)
