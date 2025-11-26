import uuid
from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_role
from app.core.types import TokenData
from app.domains.housing.category_service import HousingCategoryService
from app.literals.users import Role
from app.schemas import (
    HousingCategoryCreate,
    HousingCategoryList,
    HousingCategoryRead,
    HousingCategoryUpdate,
)

router = APIRouter()


def get_category_service(db: Session = Depends(get_db)) -> HousingCategoryService:
    """Dependency to inject HousingCategoryService."""
    return HousingCategoryService(db)


@router.post(
    "/",
    response_model=HousingCategoryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new housing category",
    response_description="Returns the newly created housing category.",
)
def create_category(
    category_in: HousingCategoryCreate,
    service: HousingCategoryService = Depends(get_category_service),
    _: TokenData = Depends(require_role(Role.ADMIN)),
):
    """
    Create a new housing category.

    This endpoint allows adding a new category (e.g., Apartment, Room, Studio)
    that can later be associated with housing offers.
    """
    return service.create_category(category_in)


@router.get(
    "/",
    response_model=List[HousingCategoryList],
    status_code=status.HTTP_200_OK,
    summary="List all housing categories",
    response_description="Returns a list of available housing categories.",
)
def list_categories(
    skip: int = 0,
    limit: int = 100,
    service: HousingCategoryService = Depends(get_category_service),
):
    """
    Retrieve a paginated list of all housing categories.

    Args:
        skip (int): Number of records to skip for pagination.
        limit (int): Maximum number of categories to return (default: 100).
    """
    return service.list_categories(skip, limit)


@router.get(
    "/{category_id}",
    response_model=HousingCategoryRead,
    status_code=status.HTTP_200_OK,
    summary="Get a housing category by ID",
    response_description="Returns a housing category matching the given ID.",
)
def get_category(
    category_id: uuid.UUID,
    service: HousingCategoryService = Depends(get_category_service),
):
    """
    Retrieve details of a specific housing category by its ID.

    Raises:
        HTTPException: If the category does not exist.
    """
    return service.get_category_by_id(category_id)


@router.patch(
    "/{category_id}",
    response_model=HousingCategoryRead,
    status_code=status.HTTP_200_OK,
    summary="Update a housing category",
    response_description="Returns the updated category information.",
)
def update_category(
    category_id: uuid.UUID,
    category_update: HousingCategoryUpdate,
    service: HousingCategoryService = Depends(get_category_service),
    _: TokenData = Depends(require_role(Role.ADMIN)),
):
    """
    Update an existing housing category.

    Raises:
        HTTPException: If the category does not exist.
    """
    return service.update_category(category_id, category_update)


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a housing category",
    response_description="Removes a housing category from the database.",
)
def delete_category(
    category_id: uuid.UUID,
    service: HousingCategoryService = Depends(get_category_service),
    _: TokenData = Depends(require_role(Role.ADMIN)),
):
    """
    Delete a specific housing category by its ID.

    Raises:
        HTTPException: If the category does not exist.
    """
    service.delete_category(category_id)
