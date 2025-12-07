import random
import string
import uuid
from typing import List

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.orm import Session
from starlette import status

from app.core.security import hash_password, verify_password
from app.core.utils import extract_constraint_info
from app.domains.user.user_repository import UserRepository
from app.literals.users import Role
from app.models import ConnectionTableModel, TermsTableModel, User, UserTermsAcceptanceTableModel
from app.schemas.user import (
    UserCreate,
    UserDetail,
    UserPasswordChange,
    UserPublic,
    UserRead,
    UserRegister,
    UserUpdate,
)


class UserService:
    """Service layer for user-related business logic."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = UserRepository(db)

    def create_user(self, user_in: UserCreate) -> UserRead:
        """
        Create a new user.
        Password is already hashed by the Pydantic validator.
        """
        try:
            user_data = user_in.model_dump()
            user = self.repository.create(user_data)
            return UserRead.model_validate(user)
        except IntegrityError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=extract_constraint_info(e),
            )

    def get_user_by_id(self, user_id: uuid.UUID) -> UserRead:
        """Retrieve a user by ID."""
        user = self.repository.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_id} not found",
            )
        return UserRead.model_validate(user)

    def get_user_detail(self, user_id: uuid.UUID) -> UserDetail:
        """
        Retrieve detailed user information including relationships.
        """
        user = self.repository.get_with_relations(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_id} not found",
            )

        user_dict = UserDetail.model_validate(user).model_dump()
        user_dict["housing_offer_count"] = len(user.housing_offers)
        user_dict["listings_active"] = sum(1 for offer in user.housing_offers if offer.status == "active")
        user_dict["housing_search_count"] = 0

        return UserDetail(**user_dict)

    def get_public_profile(self, user_id: uuid.UUID) -> UserPublic:
        """Get public profile of a user."""
        user = self.repository.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_id} not found",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        return UserPublic.model_validate(user)

    def get_user_by_email(self, email: str) -> UserRead:
        """Retrieve a user by email."""
        user = self.repository.get_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return UserRead.model_validate(user)

    def get_user_by_username(self, username: str) -> UserRead:
        """Retrieve a user by username."""
        user = self.repository.get_by_username(username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return UserRead.model_validate(user)

    def list_users(
        self,
        skip: int = 0,
        limit: int = 100,
        search: str | None = None,
    ) -> List[UserRead]:
        """List all users with optional pagination and search."""
        users = self.repository.get_all(skip=skip, limit=limit, search=search)
        return [UserRead.model_validate(user) for user in users]

    def update_user(self, user_id: uuid.UUID, user_in: UserUpdate) -> UserRead:
        """
        Update a user's information.
        Only updates fields that are explicitly set.
        """
        update_data = user_in.model_dump(exclude_unset=True)

        if "email" in update_data:
            existing = self.repository.get_by_email(update_data["email"])
            if existing and existing.id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email already in use",
                )

        if "username" in update_data:
            existing = self.repository.get_by_username(update_data["username"])
            if existing and existing.id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Username already in use",
                )

        try:
            user = self.repository.update(user_id, update_data)
            return UserRead.model_validate(user)
        except NoResultFound:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_id} not found",
            )

    def change_password(
        self,
        user_id: uuid.UUID,
        password_change: UserPasswordChange,
        verify_current: bool = True,
    ) -> UserRead:
        """
        Change a user's password.

        Args:
            user_id: The ID of the user
            password_change: The password change request
            verify_current: Whether to verify the current password (False for admin resets)
        """
        user = self.repository.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_id} not found",
            )

        if password_change.new_password != password_change.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password and confirmation do not match",
            )

        if verify_current:
            if not verify_password(password_change.current_password, user.password):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Current password is incorrect",
                )

        hashed_password = hash_password(password_change.new_password)
        user = self.repository.update_password(user_id, hashed_password)

        return UserRead.model_validate(user)

    def delete_user(self, user_id: uuid.UUID) -> None:
        """Delete a user."""
        user = self.repository.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_id} not found",
            )

        self.repository.delete(user)

    def _generate_referral_code(self, length=5) -> str:
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
            # check DB for uniqueness
            if not self.repository.get_by_referral_code(code):
                return code

    def register(
            self,
            data: UserRegister,
            ip_address: str,
            user_agent: str
    ) -> UserRead:
        """
        Public user registration (signup).
        Performs an atomic transaction:
        1. Validate inputs (Email, Username, Terms, Referral).
        2. Create User.
        3. Create UserTermsAcceptance.
        4. Create Connection log.
        5. Commit all or rollback.
        """

        # Email uniqueness
        if self.repository.exists_by_email(str(data.email)):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        # Username uniqueness
        if self.repository.exists_by_username(data.username):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already taken",
            )

        # Accepting terms, search by the version
        terms = self.db.scalar(
            select(TermsTableModel).where(TermsTableModel.version == data.accepted_terms_version)
        )
        if not terms:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid terms version: {data.accepted_terms_version}"
            )

        # Optionally validating provided referral code
        referrer_id = None
        if data.referral_code:
            referrer = self.repository.get_by_referral_code(data.referral_code)
            if not referrer:
                raise HTTPException(status_code=400, detail="Invalid referral code.")
            referrer_id = referrer.id

        new_referral_code = self._generate_referral_code()
        hashed_pw = hash_password(data.password)

        # atomic transaction
        try:
            # A. creating User
            new_user = User(
                username=data.username,
                email=data.email,  #pydantic validator make it lower().
                password=hashed_pw,
                first_name=data.first_name,
                last_name=data.last_name,
                phone=data.phone,
                referral_code=new_referral_code,
                referred_by_id=referrer_id,
                created_ip=ip_address,
                user_agent=user_agent,
                role=Role.BASIC,
                provider="local",
                is_active=True,
                is_verified=False
            )
            self.db.add(new_user)
            self.db.flush()

            # B. Creating record of accepted terms
            acceptance = UserTermsAcceptanceTableModel(
                user_id=new_user.id,
                terms_id=terms.id
            )
            self.db.add(acceptance)

            # C. Saving connection log (ip, user)
            connection = ConnectionTableModel(
                user_id=new_user.id,
                ip_address=ip_address
            )
            self.db.add(connection)

            # commit
            self.db.commit()
            self.db.refresh(new_user)

            return UserRead.model_validate(new_user)

        except IntegrityError as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=extract_constraint_info(e),
            )
        except ValueError as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Registration failed: {str(e)}"
            )