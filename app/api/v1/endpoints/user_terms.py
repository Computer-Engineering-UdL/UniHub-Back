from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.core.types import TokenData
from app.domains.terms.terms_service import TermsService
from app.domains.terms.user_terms_service import UserTermsAcceptanceService
from app.schemas.user_terms_acceptance import (
    UserTermsAcceptanceList,
    UserTermsAcceptanceRead,
)

router = APIRouter()


def get_terms_service(db: Session = Depends(get_db)) -> TermsService:
    return TermsService(db)


def get_user_terms_acceptance_service(
    db: Session = Depends(get_db),
    terms_service: TermsService = Depends(get_terms_service),
) -> UserTermsAcceptanceService:
    return UserTermsAcceptanceService(db, terms_service)


# POST /accept — accept the newest version of terms
@router.post(
    "/accept",
    response_model=UserTermsAcceptanceRead,
    status_code=status.HTTP_201_CREATED,
    summary="Accept the latest Terms version",
)
def accept_latest_terms(
    service: UserTermsAcceptanceService = Depends(get_user_terms_acceptance_service),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Accept the latest Terms version.
    """
    return service.accept_latest_terms(current_user.id)


# GET /latest-status — check if latest terms are accepted
@router.get(
    "/latest-status",
    status_code=status.HTTP_200_OK,
    summary="Check whether user accepted the latest Terms",
)
def get_terms_status(
    acceptance_service: UserTermsAcceptanceService = Depends(get_user_terms_acceptance_service),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Checks if the user accepted the latest Terms version.
    """
    latest = acceptance_service.terms_service.get_latest_terms()
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


# GET /user/list — list all terms accepted
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
    Returns all Terms versions accepted by the logged-in user.
    """
    return service.list_user_acceptances(current_user.id)
