import uuid
from typing import List

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.domains.terms.terms_repository import TermsRepository
from app.schemas import (
    TermsCreate,
    TermsDetail,
    TermsList,
    TermsRead,
    TermsUpdate,
)


class TermsService:
    """Service layer for Terms business logic."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = TermsRepository(db)

    # create
    def create_terms(self, terms_in: TermsCreate) -> TermsRead:
        try:
            terms = self.repository.create(terms_in.model_dump())
            return TermsRead.model_validate(terms)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    # read one
    def get_terms_by_id(self, terms_id: uuid.UUID) -> TermsDetail:
        terms = self.repository.get_by_id(terms_id)
        if not terms:
            raise HTTPException(status_code=404, detail="Terms not found.")

        return TermsDetail.model_validate(terms)

    def get_terms_by_version(self, version: str) -> TermsDetail:
        terms = self.repository.get_by_version(version)
        if not terms:
            raise HTTPException(status_code=404, detail="Terms not found.")

        return TermsDetail.model_validate(terms)

    def get_latest_terms(self) -> TermsDetail | None:
        """
        Returns the newest Terms entry based on creation date.
        Returns None if no Terms exist.
        """
        latest = self.repository.get_latest()
        if not latest:
            return None
        return TermsDetail.model_validate(latest)

    # list
    def list_terms(self, skip: int = 0, limit: int = 50) -> List[TermsList]:
        terms = self.repository.get_all(skip, limit)
        return [TermsList.model_validate(t) for t in terms]

    # update
    def update_terms(self, terms_id: uuid.UUID, terms_in: TermsUpdate) -> TermsRead:
        terms = self.repository.get_by_id(terms_id)
        if not terms:
            raise HTTPException(status_code=404, detail="Terms not found.")

        update_data = terms_in.model_dump(exclude_unset=True)

        try:
            updated = self.repository.update(terms, update_data)
            return TermsRead.model_validate(updated)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    # delete
    def delete_terms(self, terms_id: uuid.UUID) -> None:
        terms = self.repository.get_by_id(terms_id)
        if not terms:
            raise HTTPException(status_code=404, detail="Terms not found.")

        self.repository.delete(terms)
