from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.types import TokenData
from app.crud.housing_amenity import HousingAmenityCRUD
from app.literals.users import Role
from app.schemas import (
    HousingAmenityCreate,
    HousingAmenityRead,
)

router = APIRouter()


@router.post(
    "/",
    response_model=HousingAmenityRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new amenity",
    response_description="Returns the created amenity.",
)
def create_amenity(
    amenity_in: HousingAmenityCreate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Create a new housing amenity definition.

    **Permissions:** Admins only.
    Used to register new amenities (e.g., WIFI, PARKING, BALCONY) in the system.
    """
    if current_user.role != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to create amenities.")

    try:
        return HousingAmenityCRUD.create(db, amenity_in)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create amenity: {e}")


@router.get(
    "/{code}",
    response_model=HousingAmenityRead,
    status_code=status.HTTP_200_OK,
    summary="Get an amenity by code",
    response_description="Returns a single amenity if found.",
)
def get_amenity(
    code: int,
    db: Session = Depends(get_db),
):
    """
    Retrieve a housing amenity by its numeric OTA code.
    """
    amenity = HousingAmenityCRUD.get_by_code(db, code)
    if not amenity:
        raise HTTPException(status_code=404, detail="Amenity not found.")
    return amenity


@router.get(
    "/",
    response_model=List[HousingAmenityRead],
    status_code=status.HTTP_200_OK,
    summary="List all amenities",
    response_description="Returns all defined housing amenities.",
)
def list_amenities(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
):
    """
    Retrieve all registered amenities with optional pagination.
    """
    return HousingAmenityCRUD.get_all(db, skip=skip, limit=limit)


@router.delete(
    "/{code}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an amenity",
    response_description="Removes an amenity from the database.",
)
def delete_amenity(
    code: int,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Delete an existing amenity.

    **Permissions:** Admins only.
    Used when an amenity is deprecated or added by mistake.
    """
    if current_user.role != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to delete amenities.")

    success = HousingAmenityCRUD.delete(db, code)
    if not success:
        raise HTTPException(status_code=404, detail="Amenity not found or could not be deleted.")
    return None
