import datetime
import uuid
from typing import List

from sqlalchemy.orm import Session

from app.literals.like_status import LikeStatus, LikeTargetType
from app.models import User, UserLike


class UserLikeCRUD:
    @staticmethod
    def like_offer(
        db: Session,
        user_id: uuid.UUID,
        target_id: uuid.UUID,
        target_type: LikeTargetType = LikeTargetType.HOUSING_OFFER,
    ) -> UserLike:
        """User likes an offer."""
        existing = (
            db.query(UserLike)
            .filter(
                UserLike.user_id == user_id,
                UserLike.target_id == target_id,
                UserLike.target_type == target_type,
            )
            .first()
        )

        if existing:
            # if it was inactive, reactivate it
            if existing.status == LikeStatus.INACTIVE:
                existing.status = LikeStatus.ACTIVE
                existing.updated_at = datetime.datetime.now(datetime.UTC)
            return existing

        # if does not exist, create a new like
        new_like = UserLike(
            user_id=user_id,
            target_id=target_id,
            target_type=target_type,
            status=LikeStatus.ACTIVE,
            updated_at=datetime.datetime.now(datetime.UTC),
        )
        db.add(new_like)
        return new_like

    @staticmethod
    def unlike_offer(
        db: Session,
        user_id: uuid.UUID,
        target_id: uuid.UUID,
        current_user: User,
        target_type: LikeTargetType = LikeTargetType.HOUSING_OFFER,
    ) -> bool:
        """Mark like as inactive, allowed only for the owner or admin."""
        like = (
            db.query(UserLike)
            .filter(
                UserLike.user_id == user_id,
                UserLike.target_id == target_id,
                UserLike.target_type == target_type,
                UserLike.status == LikeStatus.ACTIVE,
            )
            .first()
        )

        if not like:
            return False

        # check if current user is owner or admin
        if like.user_id != current_user.id and not current_user.is_admin:
            raise PermissionError("You are not allowed to remove this like.")

        like.status = LikeStatus.INACTIVE
        like.updated_at = datetime.datetime.now(datetime.UTC)
        return True

    @staticmethod
    def get_user_likes(
        db: Session,
        user_id: uuid.UUID,
        current_user: User,
        target_type: LikeTargetType = LikeTargetType.HOUSING_OFFER,
        only_active: bool = True,
    ) -> List[UserLike]:
        """
        Get all (or only active) likes of a user.

        - A regular user can only see their own likes.
        - Admins can view likes of any user.
        """
        if user_id != current_user.id and not current_user.is_admin:
            raise PermissionError("You are not allowed to view likes of another user.")

        query = db.query(UserLike).filter(
            UserLike.user_id == user_id,
            UserLike.target_type == target_type,
        )
        if only_active:
            query = query.filter(UserLike.status == LikeStatus.ACTIVE)

        return query.all()

    @staticmethod
    def is_liked(
        db: Session,
        user_id: uuid.UUID,
        target_id: uuid.UUID,
        target_type: LikeTargetType = LikeTargetType.HOUSING_OFFER,
    ) -> bool:
        """
        Check if a user has liked a given offer.
        This should usually be called for the *current user* only.
        """
        return (
            db.query(UserLike)
            .filter(
                UserLike.user_id == user_id,
                UserLike.target_id == target_id,
                UserLike.target_type == target_type,
                UserLike.status == LikeStatus.ACTIVE,
            )
            .first()
            is not None
        )
