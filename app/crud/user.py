import uuid

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.orm import Session
from starlette import status

from app.core.security import hash_password
from app.crud.utils import extract_constraint_info
from app.models import User
from app.schemas import UserCreate, UserPasswordChange, UserUpdate


class UserCRUD:
    @staticmethod
    def create(db: Session, user_in: UserCreate) -> User:
        """
        Create a new user. Password should be hashed before calling this.
        """
        try:
            db_user = User(**user_in.model_dump())
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            return db_user
        except IntegrityError as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=extract_constraint_info(e),
            )

    @staticmethod
    def get_by_id(db: Session, user_id: uuid.UUID) -> User:
        stmt = select(User).where(User.id == user_id)
        user_db = db.scalar(stmt)
        if user_db is None:
            raise NoResultFound("User not found")
        print(user_db)
        return user_db

    @staticmethod
    def get_by_email(db: Session, email: str) -> User:
        stmt = select(User).where(User.email == email)
        user_db = db.scalar(stmt)
        if user_db is None:
            raise NoResultFound("User not found")
        return user_db

    @staticmethod
    def get_by_username(db: Session, username: str) -> User:
        stmt = select(User).where(User.username == username)
        user_db = db.scalar(stmt)
        if user_db is None:
            raise NoResultFound("User not found")
        return user_db

    @staticmethod
    def get_all(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        search: str | None = None,
    ) -> list[User]:
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
        return list(db.scalars(stmt).all())

    @staticmethod
    def update(db: Session, user_id: uuid.UUID, user_in: UserUpdate) -> User:
        user = UserCRUD.get_by_id(db, user_id)
        if user is None:
            raise NoResultFound("User not found")

        data = user_in.model_dump(exclude_unset=True)
        for k, v in data.items():
            setattr(user, k, v)

        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def set_password(db: Session, user_id: uuid.UUID, password_change_user: UserPasswordChange) -> User:
        user = UserCRUD.get_by_id(db, user_id)
        if user is None:
            raise NoResultFound("User not found")

        if password_change_user.new_password != password_change_user.confirm_password:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords do not match")

        hashed_password = hash_password(password_change_user.confirm_password)
        user.hashed_password = hashed_password

        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def delete(db: Session, user_id: uuid.UUID) -> bool:
        user = UserCRUD.get_by_id(db, user_id)
        db.delete(user)
        db.commit()
        return True
