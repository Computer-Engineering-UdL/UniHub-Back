import uuid
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette import status

from app.api.utils import handle_crud_errors
from app.api.utils.db_utils import extract_constraint_info
from app.core.security import hash_password
from app.models.user import User
from app.schemas import UserList, UserRead
from app.schemas.user import UserCreate, UserPasswordChange, UserUpdate


class UserCRUD:
    @staticmethod
    def create(db: Session, user_in: UserCreate) -> UserRead:
        """
        Crea un nuevo usuario. La contraseña debe venir ya hasheada.
        """
        try:
            db_user = User(**user_in.model_dump())
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            return db_user
        except IntegrityError as e:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=extract_constraint_info(e))

    @staticmethod
    @handle_crud_errors
    def get_by_id(db: Session, user_id: uuid.UUID) -> Optional[User]:
        return db.query(User).get(user_id)

    @staticmethod
    @handle_crud_errors
    def get_by_email(db: Session, email: str) -> Optional[User]:
        return db.query(User).filter_by(email=email).first()

    @staticmethod
    @handle_crud_errors
    def get_by_username(db: Session, username: str) -> Optional[User]:
        return db.query(User).filter_by(username=username).first()

    @staticmethod
    def get_all(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        search: str | None = None,
    ) -> list[type[UserList]]:
        query = db.query(User)
        if search:
            like = f"%{search}%"
            query = query.filter(
                (User.username.ilike(like))
                | (User.email.ilike(like))
                | (User.first_name.ilike(like))
                | (User.last_name.ilike(like))
            )
        return query.offset(skip).limit(limit).all()

    @staticmethod
    @handle_crud_errors
    def update(db: Session, user_id: uuid.UUID, user_in: UserUpdate) -> Optional[UserRead]:
        user = db.query(User).get(user_id)
        data = user_in.model_dump(exclude_unset=True)
        for k, v in data.items():
            setattr(user, k, v)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def set_password(db: Session, user_id: uuid.UUID, password_change_user: UserPasswordChange) -> Optional[UserRead]:
        user = db.query(User).get(user_id)
        if password_change_user.new_password != password_change_user.confirm_password:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords do not match")
        hashed_password = hash_password(password_change_user.confirm_password)
        user.hashed_password = hashed_password
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    @handle_crud_errors
    def delete(db: Session, user_id) -> bool:
        user = db.query(User).get(user_id)
        if not user:
            return False
        db.delete(user)
        db.commit()
        return True
