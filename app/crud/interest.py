import uuid
from typing import List

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.orm import Session, selectinload
from starlette import status

from app.models import Interest, InterestCategory, User


class InterestCRUD:
    @staticmethod
    def list_categories(db: Session) -> List[InterestCategory]:
        return (
            db.query(InterestCategory)
            .options(selectinload(InterestCategory.interests))
            .order_by(InterestCategory.name)
            .all()
        )

    @staticmethod
    def get_user_interests(db: Session, user_id: uuid.UUID) -> List[Interest]:
        user = db.query(User).options(selectinload(User.interests)).filter(User.id == user_id).first()

        if not user:
            raise NoResultFound("User not found")

        return list(user.interests)

    @staticmethod
    def add_interest_to_user(db: Session, user_id: uuid.UUID, interest_id: uuid.UUID) -> List[Interest]:
        user = db.query(User).options(selectinload(User.interests)).filter(User.id == user_id).first()
        if not user:
            raise NoResultFound("User not found")

        interest = db.query(Interest).filter(Interest.id == interest_id).first()
        if not interest:
            raise NoResultFound("Interest not found")

        if any(existing.id == interest_id for existing in user.interests):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Interest already added to user",
            )

        user.interests.append(interest)

        try:
            db.commit()
            db.refresh(user, attribute_names=["interests"])
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Interest already added to user (race condition)",
            )

        return list(user.interests)

    @staticmethod
    def remove_interest_from_user(db: Session, user_id: uuid.UUID, interest_id: uuid.UUID) -> bool:
        user = db.query(User).options(selectinload(User.interests)).filter(User.id == user_id).first()
        if not user:
            raise NoResultFound("User not found")

        interest = next((item for item in user.interests if item.id == interest_id), None)
        if not interest:
            raise NoResultFound("Interest not linked to the user")

        user.interests.remove(interest)
        db.commit()
        return True
