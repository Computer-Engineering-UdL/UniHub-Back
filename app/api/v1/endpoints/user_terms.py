import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.types import TokenData
from app.domains.terms.terms_service import TermsService
from app.domains.terms.user_terms_service import UserTermsAcceptanceService
from app.schemas.user_terms_acceptance import (
    UserTermsAcceptanceList,
    UserTermsAcceptanceRead,
)

router = APIRouter()


# Dependency injector
def get_user_terms_acceptance_service(
    db: Session = Depends(get_db),
) -> UserTermsAcceptanceService:
    return UserTermsAcceptanceService(db)


def get_terms_service(
    db: Session = Depends(get_db),
) -> TermsService:
    return TermsService(db)


# POST /accept/{terms_id}
@router.post(
    "/accept/{terms_id}",
    response_model=UserTermsAcceptanceRead,
    status_code=status.HTTP_201_CREATED,
    summary="Accept a Terms version",
    response_description="Returns created acceptance entry.",
)
def accept_terms(
    terms_id: uuid.UUID,
    service: UserTermsAcceptanceService = Depends(get_user_terms_acceptance_service),
    terms_service: TermsService = Depends(get_terms_service),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Accept a Terms version (logged-in user only).
    """

    # Ensure terms exists
    terms = terms_service.get_terms_by_id(terms_id)
    if terms is None:
        raise HTTPException(status_code=404, detail="Terms not found.")

    return service.accept_terms(
        user_id=current_user.id,
        terms_id=terms_id,
    )

# GET /status — acceptance of latest Terms
@router.get(
    "/latest-status",
    status_code=status.HTTP_200_OK,
    summary="Check whether user accepted the latest Terms",
)
def get_terms_status(
    acceptance_service: UserTermsAcceptanceService = Depends(get_user_terms_acceptance_service),
    terms_service: TermsService = Depends(get_terms_service),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Checks if the user accepted the latest Terms version.
    Returns the latest version and user's last acceptance.
    """

    latest = terms_service.get_latest_terms()
    if not latest:
        return {
            "latest_terms_id": None,
            "latest_version": None,
            "accepted_latest": False,
            "user_last_accepted_terms_id": None,
        }

    user_last = acceptance_service.get_last_user_acceptance(current_user.id)

    return {
        "latest_terms_id": latest.id,
        "latest_version": latest.version,
        "accepted_latest": user_last and user_last.terms_id == latest.id,
        "user_last_accepted_terms_id": user_last.terms_id if user_last else None,
    }

# GET /{acceptance_id} — get acceptance by ID
@router.get(
    "/{acceptance_id}",
    response_model=UserTermsAcceptanceRead,
    status_code=status.HTTP_200_OK,
    summary="Get Terms acceptance by ID",
    response_description="Returns single acceptance entry.",
)
def get_acceptance(
    acceptance_id: uuid.UUID,
    service: UserTermsAcceptanceService = Depends(get_user_terms_acceptance_service),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Retrieve a specific acceptance record.
    User can only read their own acceptance.
    """

    acc = service.get_by_id(acceptance_id)

    if not acc:
        raise HTTPException(status_code=404, detail="Acceptance record not found.")

    if acc.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this record.")

    return acc


# GET /user/list — all acceptances of current user
@router.get(
    "/user/list",
    response_model=List[UserTermsAcceptanceList],
    status_code=status.HTTP_200_OK,
    summary="List all Terms acceptances of current user",
)
def list_user_acceptances(
    service: UserTermsAcceptanceService = Depends(get_user_terms_acceptance_service),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Returns all Terms versions accepted by logged-in user.
    """
    return service.list_user_acceptances(current_user.id)


# GET /check/{terms_id}
@router.get(
    "/check/{terms_id}",
    status_code=status.HTTP_200_OK,
    summary="Check if user accepted a specific Terms version",
)
def check_user_terms_acceptance(
    terms_id: uuid.UUID,
    service: UserTermsAcceptanceService = Depends(get_user_terms_acceptance_service),
    terms_service: TermsService = Depends(get_terms_service),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Check whether the logged-in user accepted this specific Terms version.
    """

    # Ensure terms exists
    terms = terms_service.get_terms_by_id(terms_id)
    if not terms:
        raise HTTPException(status_code=404, detail="Terms not found.")

    acc = service.get_user_acceptance(current_user.id, terms_id)

    return {
        "terms_id": terms_id,
        "accepted": acc is not None,
        "accepted_at": acc.accepted_at if acc else None,
    }