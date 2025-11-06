import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.types import TokenData
from app.crud.user_like import UserLikeCRUD
from app.literals.like_status import LikeTargetType
from app.models import User
from app.schemas import UserLikeRead

router = APIRouter()


@router.post(
    "/{target_id}",
    response_model=UserLikeRead,
    status_code=status.HTTP_201_CREATED,
    summary="Like a target (e.g. housing offer)",
    response_description="Returns the created or reactivated like.",
)
def like_target(
    target_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
    target_type: LikeTargetType = LikeTargetType.HOUSING_OFFER,
):
    """
    Like a target object (e.g., a housing offer).

    - If a like already exists and is inactive → reactivates it.
    - If no like exists → creates a new one.
    """
    try:
        like = UserLikeCRUD.like_offer(
            db=db,
            user_id=current_user.id,
            target_id=target_id,
            target_type=target_type,
        )
        db.commit()
        db.refresh(like)
        return like
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to like target: {e}")


@router.delete(
    "/{target_id}",
    status_code=status.HTTP_200_OK,
    summary="Unlike a target (deactivate like)",
)
def unlike_target(
    target_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    target_type: LikeTargetType = LikeTargetType.HOUSING_OFFER,
):
    """
    Unlike (deactivate) a previously liked object.

    - Allowed only for the owner or admin.
    - Does *not* delete the like immediately (it’s marked as inactive).
    """
    success = UserLikeCRUD.unlike_offer(
        db=db,
        user_id=current_user.id,
        target_id=target_id,
        current_user=current_user,
        target_type=target_type,
    )

    if not success:
        raise HTTPException(status_code=404, detail="Like not found or already inactive.")

    db.commit()
    return {"detail": "Like deactivated successfully."}


@router.get(
    "/me",
    response_model=List[UserLikeRead],
    status_code=status.HTTP_200_OK,
    summary="Get current user's likes",
    response_description="Returns all active likes for the current user.",
)
def get_my_likes(
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
    only_active: bool = True,
    target_type: LikeTargetType = LikeTargetType.HOUSING_OFFER,
):
    """
    Get all (or only active) likes of the current user.
    """
    likes = UserLikeCRUD.get_user_likes(
        db=db,
        user_id=current_user.id,
        current_user=current_user,
        target_type=target_type,
        only_active=only_active,
    )
    return likes


@router.get(
    "/{target_id}/status",
    status_code=status.HTTP_200_OK,
    summary="Check if current user liked a target",
    response_description="Returns whether the current user has an active like for the given target.",
)
def check_like_status(
    target_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
    target_type: LikeTargetType = LikeTargetType.HOUSING_OFFER,
):
    """
    Check whether the current user has liked the given target.
    """
    liked = UserLikeCRUD.is_liked(
        db=db,
        user_id=current_user.id,
        target_id=target_id,
        target_type=target_type,
    )
    return {"liked": liked}
