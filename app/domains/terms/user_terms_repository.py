import uuid
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import UserTermsAcceptanceTableModel
from app.repositories.base import BaseRepository


class UserTermsAcceptanceRepository(BaseRepository[UserTermsAcceptanceTableModel]):
    """Repository for user–terms acceptance relation."""

    def __init__(self, db: Session):
        super().__init__(UserTermsAcceptanceTableModel, db)
        self.model = self.model_class

    def create(self, data: dict) -> UserTermsAcceptanceTableModel:
        """Create a new acceptance entry."""
        acceptance = UserTermsAcceptanceTableModel(**data)

        try:
            self.db.add(acceptance)
            self.db.commit()
            self.db.refresh(acceptance)
            return acceptance
        except IntegrityError:
            self.db.rollback()
            raise ValueError("Acceptance already exists for this user and terms.")
        except Exception:
            self.db.rollback()
            raise

    def get_by_id(self, acceptance_id: uuid.UUID) -> Optional[UserTermsAcceptanceTableModel]:
        stmt = select(self.model).filter(self.model.id == acceptance_id)
        return self.db.scalar(stmt)

    def get_by_user_and_terms(
        self,
        user_id: uuid.UUID,
        terms_id: uuid.UUID,
    ) -> Optional[UserTermsAcceptanceTableModel]:
        stmt = select(self.model).filter(
            self.model.user_id == user_id,
            self.model.terms_id == terms_id,
        )
        return self.db.scalar(stmt)

    def list_by_user(self, user_id: uuid.UUID) -> List[UserTermsAcceptanceTableModel]:
        stmt = (
            select(self.model)
            .filter(self.model.user_id == user_id)
            .order_by(self.model.accepted_at.desc())
        )
        return list(self.db.scalars(stmt).all())

    def get_last_by_user(self, user_id: uuid.UUID) -> Optional[UserTermsAcceptanceTableModel]:
        stmt = (
            select(self.model)
            .filter(self.model.user_id == user_id)
            .order_by(self.model.accepted_at.desc())
            .limit(1)
        )
        return self.db.scalar(stmt)
