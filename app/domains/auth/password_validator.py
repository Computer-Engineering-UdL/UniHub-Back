from __future__ import annotations

import re
import uuid
from typing import TYPE_CHECKING

from fastapi import HTTPException
from sqlalchemy.orm import Session
from starlette import status

from app.core.config import settings
from app.core.security import verify_password
from app.models import PasswordHistory

if TYPE_CHECKING:
    pass


class PasswordValidator:
    """Validates password strength and history."""

    def __init__(self, db: Session):
        self.db = db

    def validate_strength(self, password: str) -> None:
        """
        Validate password strength.

        Requirements:
        - Minimum 8 characters (configurable)
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - At least one special character
        """
        errors = []

        if len(password) < settings.PASSWORD_MIN_LENGTH:
            errors.append(f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters long")

        if not re.search(r"[A-Z]", password):
            errors.append("Password must contain at least one uppercase letter")

        if not re.search(r"[a-z]", password):
            errors.append("Password must contain at least one lowercase letter")

        if not re.search(r"\d", password):
            errors.append("Password must contain at least one digit")

        if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=\[\]\\;'/`~]", password):
            errors.append("Password must contain at least one special character")

        if errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Password does not meet requirements", "errors": errors},
            )

    def check_not_in_history(self, user_id: uuid.UUID, new_password: str) -> None:
        """
        Check that the new password hasn't been used recently.
        """
        history_entries = (
            self.db.query(PasswordHistory)
            .filter(PasswordHistory.user_id == user_id)
            .order_by(PasswordHistory.created_at.desc())
            .limit(settings.PASSWORD_HISTORY_COUNT)
            .all()
        )

        for entry in history_entries:
            if verify_password(new_password, entry.password_hash):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Password was used recently. Please choose a different password. "
                    f"You cannot reuse your last {settings.PASSWORD_HISTORY_COUNT} passwords.",
                )

    def add_to_history(self, user_id: uuid.UUID, password_hash: str) -> None:
        """Add a password hash to the user's history."""
        history_entry = PasswordHistory(
            user_id=user_id,
            password_hash=password_hash,
        )
        self.db.add(history_entry)
        self.db.flush()

    def validate_and_check_history(self, user_id: uuid.UUID, new_password: str, check_history: bool = True) -> None:
        """
        Full validation: strength + history check.
        """
        self.validate_strength(new_password)
        if check_history:
            self.check_not_in_history(user_id, new_password)
