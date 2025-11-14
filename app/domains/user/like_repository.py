import datetime
import uuid
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.literals.like_status import LikeStatus, LikeTargetType
from app.models import UserLike
from app.repositories.base import BaseRepository


class UserLikeRepository(BaseRepository[UserLike]):
    """Repository for UserLike entity."""

    def __init__(self, db: Session):
        super().__init__(UserLike, db)
        self.model = self.model_class

    def get_like(
        self,
        user_id: uuid.UUID,
        target_id: uuid.UUID,
        target_type: LikeTargetType,
    ) -> Optional[UserLike]:
        """
        Retrieve a specific like by user, target, and target type.
        """
        stmt = select(UserLike).filter(
            UserLike.user_id == user_id,
            UserLike.target_id == target_id,
            UserLike.target_type == target_type,
        )
        return self.db.scalar(stmt)

    def get_active_like(
        self,
        user_id: uuid.UUID,
        target_id: uuid.UUID,
        target_type: LikeTargetType,
    ) -> Optional[UserLike]:
        """
        Retrieve an active like by user, target, and target type.
        """
        stmt = select(UserLike).filter(
            UserLike.user_id == user_id,
            UserLike.target_id == target_id,
            UserLike.target_type == target_type,
            UserLike.status == LikeStatus.ACTIVE,
        )
        return self.db.scalar(stmt)

    def create_like(
        self,
        user_id: uuid.UUID,
        target_id: uuid.UUID,
        target_type: LikeTargetType,
    ) -> UserLike:
        """Create a new like record."""
        like = UserLike(
            user_id=user_id,
            target_id=target_id,
            target_type=target_type,
            status=LikeStatus.ACTIVE,
            updated_at=datetime.datetime.now(datetime.UTC),
        )
        self.db.add(like)
        self.db.commit()
        self.db.refresh(like)
        return like

    def reactivate_like(self, like: UserLike) -> UserLike:
        """Reactivate an inactive like."""
        like.status = LikeStatus.ACTIVE
        like.updated_at = datetime.datetime.now(datetime.UTC)
        self.db.commit()
        self.db.refresh(like)
        return like

    def deactivate_like(self, like: UserLike) -> UserLike:
        """Deactivate an active like."""
        like.status = LikeStatus.INACTIVE
        like.updated_at = datetime.datetime.now(datetime.UTC)
        self.db.commit()
        self.db.refresh(like)
        return like

    def get_user_likes(
        self,
        user_id: uuid.UUID,
        target_type: LikeTargetType,
        only_active: bool = True,
    ) -> List[UserLike]:
        """
        Retrieve all likes for a user, optionally filtered by status.
        """
        stmt = select(UserLike).filter(
            UserLike.user_id == user_id,
            UserLike.target_type == target_type,
        )

        if only_active:
            stmt = stmt.filter(UserLike.status == LikeStatus.ACTIVE)

        return list(self.db.scalars(stmt).all())

    def is_liked(
        self,
        user_id: uuid.UUID,
        target_id: uuid.UUID,
        target_type: LikeTargetType,
    ) -> bool:
        """Check if a user has an active like on a specific target."""
        return self.get_active_like(user_id, target_id, target_type) is not None

    def get_target_like_count(
        self,
        target_id: uuid.UUID,
        target_type: LikeTargetType,
    ) -> int:
        """
        Get the total number of active likes for a specific target.
        """
        from sqlalchemy import func

        stmt = select(func.count(UserLike.id)).filter(
            UserLike.target_id == target_id,
            UserLike.target_type == target_type,
            UserLike.status == LikeStatus.ACTIVE,
        )
        return self.db.scalar(stmt) or 0
