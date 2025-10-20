import uuid
from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.utils import handle_crud_errors
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.core.types import TokenData
from app.crud.user import UserCRUD
from app.literals.users import Role
from app.schemas.user import UserCreate, UserPasswordChange, UserRead, UserUpdate

router = APIRouter()


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
@handle_crud_errors()
def create_user(user_in: UserCreate, db: Session = Depends(get_db), _: TokenData = Depends(require_role(Role.ADMIN))):
    """
    Create a new user. Requires ADMIN role.
    """
    return UserCRUD.create(db, user_in)


@router.get("/me", response_model=UserRead)
@handle_crud_errors()
def get_current_user_profile(db: Session = Depends(get_db), current_user: TokenData = Depends(get_current_user)):
    """
    Get current authenticated user's profile.
    """
    return UserCRUD.get_by_id(db, current_user.id)


@router.get("/email/{email}", response_model=UserRead)
@handle_crud_errors()
def get_user_by_email(email: str, db: Session = Depends(get_db), _: TokenData = Depends(require_role(Role.ADMIN))):
    """
    Retrieve a user by email. Requires ADMIN role.
    """
    return UserCRUD.get_by_email(db, email)


@router.get("/username/{username}", response_model=UserRead)
@handle_crud_errors()
def get_user_by_username(
    username: str, db: Session = Depends(get_db), _: TokenData = Depends(require_role(Role.ADMIN))
):
    """
    Retrieve a user by username. Requires ADMIN role.
    """
    return UserCRUD.get_by_username(db, username)


@router.get("/{user_id}", response_model=UserRead)
@handle_crud_errors()
def get_user(user_id: uuid.UUID, db: Session = Depends(get_db), _: TokenData = Depends(require_role(Role.ADMIN))):
    """
    Retrieve a user by ID. Requires ADMIN role.
    """
    return UserCRUD.get_by_id(db, user_id)


@router.get("/", response_model=List[UserRead])
def list_users(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    search: str | None = None,
    _: TokenData = Depends(require_role(Role.ADMIN)),
):
    """
    Retrieve all users (with optional pagination and search). Requires ADMIN role.
    """
    return UserCRUD.get_all(db, skip=skip, limit=limit, search=search)


@router.patch("/me", response_model=UserRead)
@handle_crud_errors()
def update_current_user(
    user_in: UserUpdate, db: Session = Depends(get_db), current_user: TokenData = Depends(get_current_user)
):
    """
    Update current authenticated user's profile.
    """
    return UserCRUD.update(db, current_user.id, user_in)


@router.patch("/{user_id}", response_model=UserRead)
@handle_crud_errors()
def update_user(
    user_id: uuid.UUID,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    _: TokenData = Depends(require_role(Role.ADMIN)),
):
    """
    Update a user (partial). Requires ADMIN role.
    """
    return UserCRUD.update(db, user_id, user_in)


@router.put("/me/password", response_model=UserRead)
@handle_crud_errors()
def change_current_user_password(
    password_change: UserPasswordChange,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Change current authenticated user's password.
    """
    return UserCRUD.set_password(db, current_user.id, password_change)


@router.put("/{user_id}/password", response_model=UserRead)
@handle_crud_errors()
def change_user_password(
    user_id: uuid.UUID,
    password_change: UserPasswordChange,
    db: Session = Depends(get_db),
    _: TokenData = Depends(require_role(Role.ADMIN)),
):
    """
    Change a user's password. Requires ADMIN role.
    """
    return UserCRUD.set_password(db, user_id, password_change)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
@handle_crud_errors()
def delete_user(user_id: uuid.UUID, db: Session = Depends(get_db), _: TokenData = Depends(require_role(Role.ADMIN))):
    """
    Delete a user. Requires ADMIN role.
    """
    return UserCRUD.delete(db, user_id)
