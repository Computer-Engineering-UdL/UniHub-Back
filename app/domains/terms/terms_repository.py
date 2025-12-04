import uuid
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import TermsTableModel
from app.repositories.base import BaseRepository


class TermsRepository(BaseRepository[TermsTableModel]):
    """Repository for Terms entity."""

    def __init__(self, db: Session):
        super().__init__(TermsTableModel, db)
        self.model = self.model_class

    def create(self, data: dict) -> TermsTableModel:
        """Create a new Terms entry."""
        terms = TermsTableModel(**data)

        try:
            self.db.add(terms)
            self.db.commit()
            self.db.refresh(terms)
            return terms
        except IntegrityError:
            self.db.rollback()
            raise ValueError("Terms with this version already exists.")
        except Exception:
            self.db.rollback()
            raise

    def get_by_id(self, terms_id: uuid.UUID) -> Optional[TermsTableModel]:
        """Get terms entry by ID."""
        stmt = select(TermsTableModel).filter(TermsTableModel.id == terms_id)
        return self.db.scalar(stmt)

    def get_by_version(self, version: str) -> Optional[TermsTableModel]:
        """Get terms entry by version."""
        stmt = select(TermsTableModel).filter(TermsTableModel.version == version)
        return self.db.scalar(stmt)

    def get_all(self, skip: int = 0, limit: int = 100) -> List[TermsTableModel]:
        """List terms, newest first."""
        stmt = (
            select(TermsTableModel)
            .order_by(TermsTableModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def get_latest(self) -> Optional[TermsTableModel]:
        """Return the most recently created Terms."""
        stmt = (
            select(TermsTableModel)
            .order_by(TermsTableModel.created_at.desc())
            .limit(1)
        )
        return self.db.scalar(stmt)

    def update(self, terms: TermsTableModel, update_data: dict) -> TermsTableModel:
        """Update Terms."""
        for key, value in update_data.items():
            setattr(terms, key, value)

        try:
            self.db.commit()
            self.db.refresh(terms)
            return terms
        except IntegrityError:
            self.db.rollback()
            raise ValueError("Terms with this version already exists.")
        except Exception:
            self.db.rollback()
            raise

    def delete(self, terms: TermsTableModel) -> None:
        """Delete Terms."""
        self.db.delete(terms)
        self.db.commit()
