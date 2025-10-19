import uuid
from typing import List

from fastapi import HTTPException
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session, selectinload
from starlette import status

from app.models import Interest, InterestCategory, User


class InterestCRUD:
    @staticmethod
    def list_categories(db: Session) -> List[InterestCategory]:
        try:
            return (
                db.query(InterestCategory)
                .options(selectinload(InterestCategory.interests))
                .order_by(InterestCategory.name)
                .all()
            )
        except NoResultFound:
            raise NoResultFound("User not found")

    @staticmethod
    def get_user_interests(db: Session, user_id: uuid.UUID) -> List[Interest]:
        try:
            user = db.query(User).options(selectinload(User.interests)).filter(User.id == user_id).first()
        except NoResultFound:
            raise NoResultFound("User not found")
        return list(user.interests)

    @staticmethod
    def add_interest_to_user(db: Session, user_id: uuid.UUID, interest_id: uuid.UUID) -> List[Interest]:
        try:
            user = db.query(User).options(selectinload(User.interests)).filter(User.id == user_id).first()
        except NoResultFound:
            raise NoResultFound("User not found")

        interest = db.query(Interest).filter(Interest.id == interest_id).first()
        if not interest:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interest not found")

        if any(existing.id == interest_id for existing in user.interests):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Interest already added to user",
            )

        user.interests.append(interest)
        db.commit()
        db.refresh(user, attribute_names=["interests"])
        return list(user.interests)

    @staticmethod
    def remove_interest_from_user(db: Session, user_id: uuid.UUID, interest_id: uuid.UUID) -> bool:
        try:
            user = db.query(User).options(selectinload(User.interests)).filter(User.id == user_id).first()
        except NoResultFound:
            raise NoResultFound("User not found")
        interest = next((item for item in user.interests if item.id == interest_id), None)
        if not interest:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interest not linked to user")

        user.interests.remove(interest)
        db.commit()
        return True
