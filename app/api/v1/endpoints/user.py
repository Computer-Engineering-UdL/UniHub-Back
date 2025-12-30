import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, require_role
from app.api.utils import handle_api_errors
from app.core.database import get_db
from app.core.types import TokenData
from app.domains.user.user_service import UserService
from app.literals.users import Role
from app.schemas.user import (
    UserCreate,
    UserDetail,
    UserPasswordChange,
    UserPublic,
    UserRead,
    UserUpdate,
)

router = APIRouter()


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    """Dependency to inject UserService."""
    return UserService(db)


ADMIN_ONLY_FIELDS = {"role", "is_verified"}


def _filter_admin_only_fields(user_in: UserUpdate) -> UserUpdate:
    """Remove admin-only fields from update payload for non-admin users."""
    data = user_in.model_dump(exclude_unset=True)
    for field in ADMIN_ONLY_FIELDS:
        data.pop(field, None)
    return UserUpdate(**data)


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
@handle_api_errors()
def create_user(
    user_in: UserCreate,
    service: UserService = Depends(get_user_service),
    _: TokenData = Depends(require_role(Role.ADMIN)),
):
    """
    Create a new user. Requires ADMIN role.
    """
    return service.create_user(user_in)


@router.get("/me", response_model=UserDetail)
@handle_api_errors()
def get_current_user_profile(
    service: UserService = Depends(get_user_service),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Get current authenticated user's profile.
    """
    return service.get_user_detail(current_user.id)


@router.get("/{user_id}", response_model=UserDetail)
@handle_api_errors()
def get_user(
    user_id: uuid.UUID,
    service: UserService = Depends(get_user_service),
    _: TokenData = Depends(require_role(Role.ADMIN)),
):
    """
    Retrieve a user by ID. Requires ADMIN role.
    """
    return service.get_user_detail(user_id)


@router.get("/", response_model=List[UserRead])
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    search: str | None = None,
    service: UserService = Depends(get_user_service),
    _: TokenData = Depends(require_role(Role.ADMIN)),
):
    """
    Retrieve all users (with optional pagination and search). Requires ADMIN role.
    """
    return service.list_users(skip=skip, limit=limit, search=search)


@router.patch("/me", response_model=UserRead)
@handle_api_errors()
def update_current_user(
    user_in: UserUpdate,
    service: UserService = Depends(get_user_service),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Update current authenticated user's profile.
    """
    if current_user.role != Role.ADMIN:
        user_in = _filter_admin_only_fields(user_in)
    return service.update_user(current_user.id, user_in)


@router.patch("/{user_id}", response_model=UserRead)
@handle_api_errors()
def update_user(
    user_id: uuid.UUID,
    user_in: UserUpdate,
    service: UserService = Depends(get_user_service),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Update a user (partial). Users can update their own profile; admins can update any user.
    """
    if current_user.id != user_id and current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own profile",
        )
    if current_user.role != Role.ADMIN:
        user_in = _filter_admin_only_fields(user_in)
    return service.update_user(user_id, user_in)


@router.put("/me/password", response_model=UserRead)
@handle_api_errors()
def change_current_user_password(
    password_change: UserPasswordChange,
    service: UserService = Depends(get_user_service),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Change current authenticated user's password.
    """
    return service.change_password(current_user.id, password_change, verify_current=True)


@router.put("/{user_id}/password", response_model=UserRead)
@handle_api_errors()
def change_user_password(
    user_id: uuid.UUID,
    password_change: UserPasswordChange,
    service: UserService = Depends(get_user_service),
    _: TokenData = Depends(require_role(Role.ADMIN)),
):
    """
    Change a user's password. Requires ADMIN role.
    Admin password changes don't verify current password.
    """
    return service.change_password(user_id, password_change, verify_current=False)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
@handle_api_errors()
def delete_user(
    user_id: uuid.UUID,
    service: UserService = Depends(get_user_service),
    _: TokenData = Depends(require_role(Role.ADMIN)),
):
    """
    Delete a user. Requires ADMIN role.
    """
    service.delete_user(user_id)


@router.get("/public/{user_id}", response_model=UserPublic)
@handle_api_errors()
def get_public_user_profile(
    user_id: uuid.UUID,
    service: UserService = Depends(get_user_service),
):
    """
    Get public profile of a user by ID.
    """
    return service.get_public_profile(user_id)
