import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_role
from app.core.types import TokenData
from app.crud.housing_category import HousingCategoryCRUD
from app.literals.users import Role
from app.schemas import (
    HousingCategoryCreate,
    HousingCategoryList,
    HousingCategoryRead,
    HousingCategoryUpdate,
)

router = APIRouter(
    prefix="/categories",
    tags=["housing categories"],
)


@router.post(
    "/",
    response_model=HousingCategoryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new housing category",
    response_description="Returns the newly created housing category.",
)
def create_category(
    category_in: HousingCategoryCreate,
    db: Session = Depends(get_db),
    _: TokenData = Depends(require_role(Role.ADMIN)),
):
    """
    Create a new housing category.

    This endpoint allows adding a new category (e.g., Apartment, Room, Studio)
    that can later be associated with housing offers.
    """
    return HousingCategoryCRUD.create(db, category_in)


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
    db: Session = Depends(get_db),
):
    """
    Retrieve a paginated list of all housing categories.

    Args:
        skip (int): Number of records to skip for pagination.
        limit (int): Maximum number of categories to return (default: 100).
    """
    return HousingCategoryCRUD.list(db, skip=skip, limit=limit)


@router.get(
    "/{category_id}",
    response_model=HousingCategoryRead,
    status_code=status.HTTP_200_OK,
    summary="Get a housing category by ID",
    response_description="Returns a housing category matching the given ID.",
)
def get_category(
    category_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """
    Retrieve details of a specific housing category by its ID.

    Raises:
        HTTPException: If the category does not exist.
    """
    category = HousingCategoryCRUD.get_by_id(db, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found.")
    return category


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
    db: Session = Depends(get_db),
    _: TokenData = Depends(require_role(Role.ADMIN)),
):
    """
    Update an existing housing category.

    Raises:
        HTTPException: If the category does not exist.
    """
    category = HousingCategoryCRUD.update(db, category_id, category_update)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found.")
    return category


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a housing category",
    response_description="Removes a housing category from the database.",
)
def delete_category(
    category_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: TokenData = Depends(require_role(Role.ADMIN)),
):
    """
    Delete a specific housing category by its ID.

    Raises:
        HTTPException: If the category does not exist.
    """
    success = HousingCategoryCRUD.delete(db, category_id)
    if not success:
        raise HTTPException(status_code=404, detail="Category not found.")
