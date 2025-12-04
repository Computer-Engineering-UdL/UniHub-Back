import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.types import TokenData
from app.domains.terms.terms_service import TermsService
from app.literals.users import Role
from app.schemas import (
    TermsCreate,
    TermsDetail,
    TermsList,
    TermsRead,
    TermsUpdate,
)

router = APIRouter()


def get_terms_service(db: Session = Depends(get_db)) -> TermsService:
    """Dependency to inject TermsService."""
    return TermsService(db)


# create terms (admin)
@router.post(
    "/",
    response_model=TermsRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new Terms version",
    response_description="Returns the created Terms object.",
)
def create_terms(
    terms_in: TermsCreate,
    service: TermsService = Depends(get_terms_service),
    current_user: TokenData = Depends(get_current_user),
):
    """Create a new Terms entry. Only admins can create."""
    if current_user.role != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Admin privileges required.")

    return service.create_terms(terms_in)


# get by id
@router.get(
    "/{terms_id}",
    response_model=TermsDetail,
    status_code=status.HTTP_200_OK,
    summary="Get Terms by ID",
    response_description="Returns a specific Terms entry.",
)
def get_terms(
    terms_id: uuid.UUID,
    service: TermsService = Depends(get_terms_service),
    current_user: TokenData = Depends(get_current_user),
):
    """Get Terms by ID (any logged-in user)."""
    return service.get_terms_by_id(terms_id)


# get by version
@router.get(
    "/version/{version}",
    response_model=TermsDetail,
    status_code=status.HTTP_200_OK,
    summary="Get Terms by version label",
    response_description="Returns Terms with given version.",
)
def get_terms_by_version(
    version: str,
    service: TermsService = Depends(get_terms_service),
    current_user: TokenData = Depends(get_current_user),
):
    """Get Terms by version string."""
    return service.get_terms_by_version(version)


# list offers
@router.get(
    "/",
    response_model=List[TermsList],
    status_code=status.HTTP_200_OK,
    summary="List all Terms versions",
    response_description="Returns a paginated list of Terms.",
)
def list_terms(
    service: TermsService = Depends(get_terms_service),
    current_user: TokenData = Depends(get_current_user),
    skip: int = 0,
    limit: int = 50,
):
    """List all Terms (newest first)."""
    return service.list_terms(skip=skip, limit=limit)


# update terms (admin)
@router.patch(
    "/{terms_id}",
    response_model=TermsRead,
    status_code=status.HTTP_200_OK,
    summary="Update existing Terms",
    response_description="Returns the updated Terms entry.",
)
def update_terms(
    terms_id: uuid.UUID,
    terms_update: TermsUpdate,
    service: TermsService = Depends(get_terms_service),
    current_user: TokenData = Depends(get_current_user),
):
    """Only admins can update Terms."""
    if current_user.role != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Admin privileges required.")

    return service.update_terms(terms_id, terms_update)


# delete terms (admin)
@router.delete(
    "/{terms_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a Terms version",
    response_description="Removes the Terms entry.",
)
def delete_terms(
    terms_id: uuid.UUID,
    service: TermsService = Depends(get_terms_service),
    current_user: TokenData = Depends(get_current_user),
):
    """Admin-only deletion of Terms."""
    if current_user.role != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Admin privileges required.")

    service.delete_terms(terms_id)
