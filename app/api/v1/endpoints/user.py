import uuid
from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.utils import handle_crud_errors
from app.core.database import get_db
from app.crud.user import UserCRUD
from app.schemas.user import UserCreate, UserRead, UserUpdate

router = APIRouter()


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
@handle_crud_errors
def create_user(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user.
    """
    return UserCRUD.create(db, user_in)


@router.get("/{user_id}", response_model=UserRead)
@handle_crud_errors
def get_user(user_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Retrieve a user by ID.
    """
    return UserCRUD.get_by_id(db, user_id)


@router.get("/", response_model=List[UserRead])
@handle_crud_errors
def list_users(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    search: str | None = None,
):
    """
    Retrieve all users (with optional pagination and search).
    """
    return UserCRUD.get_all(db, skip=skip, limit=limit, search=search)


@router.patch("/{user_id}", response_model=UserRead)
@handle_crud_errors
def update_user(user_id: uuid.UUID, user_in: UserUpdate, db: Session = Depends(get_db)):
    """
    Update a user (partial).
    """
    return UserCRUD.update(db, user_id, user_in)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
@handle_crud_errors
def delete_user(user_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Delete a user.
    """
    return UserCRUD.delete(db, user_id)
