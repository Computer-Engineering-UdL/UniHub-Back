import uuid
from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.core.types import TokenData
from app.domains.user.like_service import UserLikeService
from app.literals.like_status import LikeTargetType
from app.schemas.user_like import UserLikeRead

router = APIRouter()


def get_like_service(db: Session = Depends(get_db)) -> UserLikeService:
    """Dependency to inject UserLikeService."""
    return UserLikeService(db)


@router.post(
    "/{target_id}",
    response_model=UserLikeRead,
    status_code=status.HTTP_201_CREATED,
    summary="Like a target (e.g. housing offer)",
    response_description="Returns the created or reactivated like.",
)
def like_target(
    target_id: uuid.UUID,
    target_type: LikeTargetType = LikeTargetType.HOUSING_OFFER,
    service: UserLikeService = Depends(get_like_service),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Like a target object (e.g., a housing offer).

    - If a like already exists and is inactive → reactivates it.
    - If no like exists → creates a new one.
    - If like is already active → returns existing like.
    """
    return service.like_target(
        user_id=current_user.id,
        target_id=target_id,
        target_type=target_type,
    )


@router.delete(
    "/{target_id}",
    status_code=status.HTTP_200_OK,
    summary="Unlike a target (deactivate like)",
)
def unlike_target(
    target_id: uuid.UUID,
    target_type: LikeTargetType = LikeTargetType.HOUSING_OFFER,
    service: UserLikeService = Depends(get_like_service),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Unlike (deactivate) a previously liked object.

    - Allowed only for the owner or admin.
    - Does *not* delete the like immediately (it's marked as inactive).
    """
    service.unlike_target(
        user_id=current_user.id,
        target_id=target_id,
        target_type=target_type,
        current_user_id=current_user.id,
        is_admin=current_user.role.lower() == "admin",
    )

    return {"detail": "Like deactivated successfully."}


@router.get(
    "/me",
    response_model=List[UserLikeRead],
    status_code=status.HTTP_200_OK,
    summary="Get current user's likes",
    response_description="Returns all active likes for the current user.",
)
def get_my_likes(
    only_active: bool = True,
    target_type: LikeTargetType = LikeTargetType.HOUSING_OFFER,
    service: UserLikeService = Depends(get_like_service),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Get all (or only active) likes of the current user.
    """
    return service.get_user_likes(
        user_id=current_user.id,
        target_type=target_type,
        current_user_id=current_user.id,
        is_admin=current_user.role.lower() == "admin",
        only_active=only_active,
    )


@router.get(
    "/{target_id}/status",
    status_code=status.HTTP_200_OK,
    summary="Check if current user liked a target",
    response_description="Returns whether the current user has an active like for the given target.",
)
def check_like_status(
    target_id: uuid.UUID,
    target_type: LikeTargetType = LikeTargetType.HOUSING_OFFER,
    service: UserLikeService = Depends(get_like_service),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Check whether the current user has liked the given target.
    """
    liked = service.check_like_status(
        user_id=current_user.id,
        target_id=target_id,
        target_type=target_type,
    )
    return {"liked": liked}
