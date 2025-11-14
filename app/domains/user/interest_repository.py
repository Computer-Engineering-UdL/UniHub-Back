import uuid
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Interest, InterestCategory, User
from app.repositories.base import BaseRepository


class InterestCategoryRepository(BaseRepository[InterestCategory]):
    """Repository for InterestCategory entity."""

    def __init__(self, db: Session):
        super().__init__(InterestCategory, db)
        self.model = self.model_class

    def get_all_with_interests(self) -> List[InterestCategory]:
        """Retrieve all interest categories with their interests."""
        stmt = (
            select(InterestCategory).options(selectinload(InterestCategory.interests)).order_by(InterestCategory.name)
        )
        return list(self.db.scalars(stmt).all())


class InterestRepository(BaseRepository[Interest]):
    """Repository for Interest entity."""

    def __init__(self, db: Session):
        super().__init__(Interest, db)
        self.model = self.model_class
        self.category_repo = InterestCategoryRepository(db)

    def get_all_categories(self) -> List[InterestCategory]:
        """Retrieve all interest categories with their interests."""
        return self.category_repo.get_all_with_interests()

    def get_category_by_id(self, category_id: uuid.UUID) -> Optional[InterestCategory]:
        """Retrieve an interest category by ID."""
        return self.category_repo.get_by_id(category_id)

    def get_interest_by_id(self, interest_id: uuid.UUID) -> Optional[Interest]:
        """Retrieve an interest by ID."""
        return self.get_by_id(interest_id)

    def get_user_interests(self, user_id: uuid.UUID) -> Optional[User]:
        """
        Retrieve a user with their interests loaded.
        Returns None if user not found.
        """
        stmt = select(User).options(selectinload(User.interests)).filter(User.id == user_id)
        return self.db.scalar(stmt)

    def add_interest_to_user(self, user: User, interest: Interest) -> User:
        """
        Add an interest to a user's profile.
        Assumes user and interest objects are already loaded.
        """
        user.interests.append(interest)
        self.db.commit()
        self.db.refresh(user, attribute_names=["interests"])
        return user

    def remove_interest_from_user(self, user: User, interest: Interest) -> User:
        """
        Remove an interest from a user's profile.
        Assumes user and interest objects are already loaded.
        """
        user.interests.remove(interest)
        self.db.commit()
        self.db.refresh(user, attribute_names=["interests"])
        return user

    def user_has_interest(self, user: User, interest_id: uuid.UUID) -> bool:
        """Check if a user already has a specific interest."""
        return any(existing.id == interest_id for existing in user.interests)
