import uuid
from typing import List

from fastapi import HTTPException
from sqlalchemy.orm import Session
from starlette import status

from app.domains.user.like_repository import UserLikeRepository
from app.literals.like_status import LikeStatus, LikeTargetType
from app.schemas.user_like import UserLikeRead


class UserLikeService:
    """Service layer for user like-related business logic."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = UserLikeRepository(db)

    def like_target(
        self,
        user_id: uuid.UUID,
        target_id: uuid.UUID,
        target_type: LikeTargetType,
    ) -> UserLikeRead:
        """
        Like a target (e.g., housing offer).

        - If a like exists and is inactive → reactivates it
        - If no like exists → creates a new one
        - If like is already active → returns existing like
        """
        existing_like = self.repository.get_like(user_id, target_id, target_type)

        if existing_like:
            if existing_like.status == LikeStatus.INACTIVE:
                like = self.repository.reactivate_like(existing_like)
            else:
                like = existing_like
        else:
            like = self.repository.create_like(user_id, target_id, target_type)

        return UserLikeRead.model_validate(like)

    def unlike_target(
        self,
        user_id: uuid.UUID,
        target_id: uuid.UUID,
        target_type: LikeTargetType,
        current_user_id: uuid.UUID,
        is_admin: bool,
    ) -> None:
        """
        Unlike (deactivate) a previously liked target.

        Only the owner or an admin can unlike.
        """
        like = self.repository.get_active_like(user_id, target_id, target_type)

        if not like:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Like not found or already inactive",
            )

        if like.user_id != current_user_id and not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not allowed to remove this like",
            )

        self.repository.deactivate_like(like)

    def get_user_likes(
        self,
        user_id: uuid.UUID,
        target_type: LikeTargetType,
        current_user_id: uuid.UUID,
        is_admin: bool,
        only_active: bool = True,
    ) -> List[UserLikeRead]:
        """
        Get all (or only active) likes for a user.

        Regular users can only see their own likes.
        Admins can view likes of any user.
        """

        if user_id != current_user_id and not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not allowed to view likes of another user",
            )

        likes = self.repository.get_user_likes(user_id, target_type, only_active)
        return [UserLikeRead.model_validate(like) for like in likes]

    def check_like_status(
        self,
        user_id: uuid.UUID,
        target_id: uuid.UUID,
        target_type: LikeTargetType,
    ) -> bool:
        """
        Check if a user has liked a specific target.
        Returns True if an active like exists.
        """
        return self.repository.is_liked(user_id, target_id, target_type)

    def get_target_like_count(
        self,
        target_id: uuid.UUID,
        target_type: LikeTargetType,
    ) -> int:
        """
        Get the total number of active likes for a specific target.
        """
        return self.repository.get_target_like_count(target_id, target_type)
