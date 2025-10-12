import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field, HttpUrl
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_password_hash  # Asumiendo que existe; si no, crea uno
from app.crud.user import UserCRUD
from app.models.user import UserPublic

router = APIRouter()


class UserCreate(BaseModel):
    username: str = Field(min_length=1, max_length=20)
    email: EmailStr
    first_name: str = Field(min_length=1, max_length=30)
    last_name: str = Field(min_length=1, max_length=30)
    password: str = Field(min_length=8)
    provider: str | None = "local"
    role: str | None = "Basic"
    avatar_url: HttpUrl | None = None
    phone: str | None = None
    university: str | None = None


class UserUpdate(BaseModel):
    username: str | None = Field(None, min_length=1, max_length=20)
    email: EmailStr | None = None
    first_name: str | None = Field(None, min_length=1, max_length=30)
    last_name: str | None = Field(None, min_length=1, max_length=30)
    password: str | None = Field(None, min_length=8)
    provider: str | None = None
    role: str | None = None
    avatar_url: HttpUrl | None = None
    phone: str | None = None
    university: str | None = None


@router.post("/", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def create_user(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user.
    """
    if UserCRUD.get_by_email(db, user_in.email):
        raise HTTPException(status_code=409, detail="Email already in use")
    if UserCRUD.get_by_username(db, user_in.username):
        raise HTTPException(status_code=409, detail="Username already in use")

    hashed = get_password_hash(user_in.password)
    try:
        user = UserCRUD.create(db, user_in=user_in, hashed_password=hashed)
        return user
    except IntegrityError:
        raise HTTPException(status_code=409, detail="User already exists")


@router.get("/{user_id}", response_model=UserPublic)
def get_user(user_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Retrieve a user by ID.
    """
    user = UserCRUD.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/", response_model=List[UserPublic])
def list_users(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    search: str | None = None,
):
    """
    List users with optional search & pagination.
    """
    return UserCRUD.get_all(db, skip=skip, limit=limit, search=search)


@router.patch("/{user_id}", response_model=UserPublic)
def update_user(user_id: uuid.UUID, user_in: UserUpdate, db: Session = Depends(get_db)):
    """
    Update a user (partial).
    """
    if user_in.password:
        hashed = get_password_hash(user_in.password)
        user_in_dict = user_in.model_dump(exclude_unset=True)
        user_in_dict.pop("password", None)
        updated = UserCRUD.update(db, user_id, UserUpdate(**user_in_dict))
        if not updated:
            raise HTTPException(status_code=404, detail="User not found")
        UserCRUD.set_password(db, user_id, hashed)
        return UserCRUD.get_by_id(db, user_id)

    updated = UserCRUD.update(db, user_id, user_in)
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")
    return updated


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Delete a user.
    """
    ok = UserCRUD.delete(db, user_id)
    if not ok:
        raise HTTPException(status_code=404, detail="User not found")
    return None
