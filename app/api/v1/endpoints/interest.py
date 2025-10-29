import uuid
from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.utils import handle_api_errors
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.types import TokenData
from app.crud.interest import InterestCRUD
from app.literals.users import Role
from app.schemas.interest import InterestCategoryRead, InterestRead, UserInterestCreate

router = APIRouter()


@router.get("/", response_model=List[InterestCategoryRead])
@handle_api_errors()
def list_interest_categories(db: Session = Depends(get_db)):
    """Return all interest categories with their interests."""

    return InterestCRUD.list_categories(db)


@router.get("/user/{user_id}", response_model=List[InterestRead])
@handle_api_errors()
def list_user_interests(user_id: uuid.UUID, db: Session = Depends(get_db)):
    """Return the interests linked to a specific user."""

    return InterestCRUD.get_user_interests(db, user_id)


@router.post(
    "/user/{user_id}",
    response_model=List[InterestRead],
    status_code=status.HTTP_201_CREATED,
)
@handle_api_errors()
def add_interest_to_user(
    user_id: uuid.UUID,
    payload: UserInterestCreate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Attach an interest to a user and return the updated list."""
    if current_user.id != user_id and current_user.role != Role.ADMIN:
        from fastapi import HTTPException

        raise HTTPException(status_code=403, detail="Not authorized to modify this user's interests.")

    return InterestCRUD.add_interest_to_user(db, user_id, payload.interest_id)


@router.delete(
    "/user/{user_id}/{interest_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
@handle_api_errors()
def remove_interest_from_user(
    user_id: uuid.UUID,
    interest_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Remove an interest from a user."""
    if current_user.id != user_id and current_user.role != Role.ADMIN:
        from fastapi import HTTPException

        raise HTTPException(status_code=403, detail="Not authorized to modify this user's interests.")

    InterestCRUD.remove_interest_from_user(db, user_id, interest_id)
    return True
