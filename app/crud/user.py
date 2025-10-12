from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import UserTableModel
from app.schemas.user import UserCreate, UserUpdate


class UserCRUD:
    @staticmethod
    def create(db: Session, user_in: UserCreate, hashed_password: str) -> UserTableModel:
        """
        Crea un nuevo usuario. La contraseña debe venir ya hasheada.
        """
        db_user = UserTableModel(
            username=user_in.username,
            email=user_in.email,
            hashed_password=hashed_password,
            first_name=user_in.first_name,
            last_name=user_in.last_name,
            provider=user_in.provider or "local",
            role=user_in.role or "Basic",
            avatar_url=user_in.avatar_url,
            phone=user_in.phone,
            university=user_in.university,
        )
        try:
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            return db_user
        except IntegrityError as e:
            db.rollback()
            raise e

    @staticmethod
    def get_by_id(db: Session, user_id) -> Optional[UserTableModel]:
        return db.query(UserTableModel).get(user_id)

    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[UserTableModel]:
        return db.query(UserTableModel).filter(UserTableModel.email == email).first()

    @staticmethod
    def get_by_username(db: Session, username: str) -> Optional[UserTableModel]:
        return db.query(UserTableModel).filter(UserTableModel.username == username).first()

    @staticmethod
    def get_all(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        search: str | None = None,
    ) -> list[UserTableModel]:
        query = db.query(UserTableModel)
        if search:
            like = f"%{search}%"
            query = query.filter(
                (UserTableModel.username.ilike(like))
                | (UserTableModel.email.ilike(like))
                | (UserTableModel.first_name.ilike(like))
                | (UserTableModel.last_name.ilike(like))
            )
        return query.offset(skip).limit(limit).all()

    @staticmethod
    def update(db: Session, user_id, user_in: UserUpdate) -> Optional[UserTableModel]:
        user = UserCRUD.get_by_id(db, user_id)
        if not user:
            return None

        data = user_in.model_dump(exclude_unset=True)
        data.pop("password", None)

        for k, v in data.items():
            setattr(user, k, v)

        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def set_password(db: Session, user_id, hashed_password: str) -> Optional[UserTableModel]:
        user = UserCRUD.get_by_id(db, user_id)
        if not user:
            return None
        user.hashed_password = hashed_password
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def delete(db: Session, user_id) -> bool:
        user = UserCRUD.get_by_id(db, user_id)
        if not user:
            return False
        db.delete(user)
        db.commit()
        return True
