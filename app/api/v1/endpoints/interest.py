import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.utils import handle_api_errors
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.types import TokenData
from app.domains.user.interest_service import InterestService
from app.literals.users import Role
from app.schemas.interest import InterestCategoryRead, InterestRead, UserInterestCreate

router = APIRouter()


def get_interest_service(db: Session = Depends(get_db)) -> InterestService:
    """Dependency to inject InterestService."""
    return InterestService(db)


@router.get("/", response_model=List[InterestCategoryRead])
def list_interest_categories(
    service: InterestService = Depends(get_interest_service),
):
    """
    Return all interest categories with their interests.
    Public endpoint - no authentication required.
    """
    return service.list_categories()


@router.get("/user/{user_id}", response_model=List[InterestRead])
@handle_api_errors()
def list_user_interests(
    user_id: uuid.UUID,
    service: InterestService = Depends(get_interest_service),
):
    """
    Return the interests linked to a specific user.
    Public endpoint - visible to all users.
    """
    return service.get_user_interests(user_id)


@router.post(
    "/user/{user_id}",
    response_model=List[InterestRead],
    status_code=status.HTTP_201_CREATED,
)
def add_interest_to_user(
    user_id: uuid.UUID,
    payload: UserInterestCreate,
    service: InterestService = Depends(get_interest_service),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Attach an interest to a user and return the updated list.

    Users can only modify their own interests unless they are an admin.
    """

    if current_user.id != user_id and current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this user's interests",
        )

    return service.add_interest_to_user(user_id, payload.interest_id)


@router.delete(
    "/user/{user_id}/{interest_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_interest_from_user(
    user_id: uuid.UUID,
    interest_id: uuid.UUID,
    service: InterestService = Depends(get_interest_service),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Remove an interest from a user.

    Users can only modify their own interests unless they are an admin.
    """

    if current_user.id != user_id and current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this user's interests",
        )

    service.remove_interest_from_user(user_id, interest_id)
