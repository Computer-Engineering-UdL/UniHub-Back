import uuid
from typing import List

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette import status

from app.domains.user.interest_repository import InterestRepository
from app.schemas.interest import InterestCategoryRead, InterestRead


class InterestService:
    """Service layer for interest-related business logic."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = InterestRepository(db)

    def list_categories(self) -> List[InterestCategoryRead]:
        """
        Retrieve all interest categories with their associated interests.
        """
        categories = self.repository.get_all_categories()
        return [InterestCategoryRead.model_validate(cat) for cat in categories]

    def get_user_interests(self, user_id: uuid.UUID) -> List[InterestRead]:
        """
        Retrieve all interests associated with a specific user.
        """
        user = self.repository.get_user_interests(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_id} not found",
            )

        return [InterestRead.model_validate(interest) for interest in user.interests]

    def add_interest_to_user(
        self,
        user_id: uuid.UUID,
        interest_id: uuid.UUID,
    ) -> List[InterestRead]:
        """
        Add an interest to a user's profile.
        Returns the updated list of user interests.
        """

        user = self.repository.get_user_interests(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_id} not found",
            )

        interest = self.repository.get_interest_by_id(interest_id)
        if not interest:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Interest with id {interest_id} not found",
            )

        if self.repository.user_has_interest(user, interest_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Interest already added to user",
            )

        try:
            user = self.repository.add_interest_to_user(user, interest)
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Interest already added to user (race condition)",
            )

        return [InterestRead.model_validate(interest) for interest in user.interests]

    def remove_interest_from_user(
        self,
        user_id: uuid.UUID,
        interest_id: uuid.UUID,
    ) -> None:
        """
        Remove an interest from a user's profile.
        """

        user = self.repository.get_user_interests(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_id} not found",
            )

        interest = next((i for i in user.interests if i.id == interest_id), None)
        if not interest:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interest not linked to the user",
            )

        self.repository.remove_interest_from_user(user, interest)
