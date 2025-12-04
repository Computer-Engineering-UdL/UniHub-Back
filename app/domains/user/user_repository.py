import uuid
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.orm import Session, selectinload

from app.models import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User entity with specialized queries."""

    def __init__(self, db: Session):
        super().__init__(User, db)

    def create(self, user_data: dict) -> User:
        """Create a new user with the provided data."""
        try:
            user = User(**user_data)
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            return user
        except IntegrityError:
            self.db.rollback()
            raise

    def get_by_email(self, email: str) -> Optional[User]:
        """Retrieve a user by email address."""
        stmt = select(User).where(User.email == email)
        return self.db.scalar(stmt)

    def get_by_username(self, username: str) -> Optional[User]:
        """Retrieve a user by username."""
        stmt = select(User).where(User.username == username)
        return self.db.scalar(stmt)

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
    ) -> List[User]:
        """
        Retrieve all users with optional pagination and search.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            search: Optional search term to filter users
        """
        stmt = select(User)

        if search:
            like = f"%{search}%"
            stmt = stmt.filter(
                (User.username.ilike(like))
                | (User.email.ilike(like))
                | (User.first_name.ilike(like))
                | (User.last_name.ilike(like))
            )

        stmt = stmt.offset(skip).limit(limit)
        return list(self.db.scalars(stmt).all())

    def get_with_relations(self, user_id: uuid.UUID) -> Optional[User]:
        """
        Retrieve a user with all relationships loaded.
        Useful for detailed user profiles.
        """
        stmt = (
            select(User)
            .where(User.id == user_id)
            .options(
                selectinload(User.faculty),
                selectinload(User.interests),
                selectinload(User.housing_offers),
            )
        )
        return self.db.scalar(stmt)

    def update(self, user_id: uuid.UUID, update_data: dict) -> User:
        """Update a user with the provided data."""
        user = self.get_by_id(user_id)
        if not user:
            raise NoResultFound(f"User with id {user_id} not found")

        for key, value in update_data.items():
            if hasattr(user, key):
                setattr(user, key, value)

        self.db.commit()
        self.db.refresh(user)
        return user

    def update_password(self, user_id: uuid.UUID, hashed_password: str) -> User:
        """Update user's password with a pre-hashed value."""
        user = self.get_by_id(user_id)
        if not user:
            raise NoResultFound(f"User with id {user_id} not found")

        user.password = hashed_password
        self.db.commit()
        self.db.refresh(user)
        return user

    def exists_by_email(self, email: str) -> bool:
        """Check if a user with the given email exists."""
        stmt = select(User.id).where(User.email == email)
        return self.db.scalar(stmt) is not None

    def exists_by_username(self, username: str) -> bool:
        """Check if a user with the given username exists."""
        stmt = select(User.id).where(User.username == username)
        return self.db.scalar(stmt) is not None

    def get_by_referral_code(self, code):
        pass
