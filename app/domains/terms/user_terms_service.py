import uuid
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.domains.terms.user_terms_repository import (
    UserTermsAcceptanceRepository,
)
from app.schemas.user_terms_acceptance import (
    UserTermsAcceptanceCreate,
    UserTermsAcceptanceList,
    UserTermsAcceptanceRead,
)


class UserTermsAcceptanceService:
    """Service layer for user–terms acceptance logic."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = UserTermsAcceptanceRepository(db)

    def accept_terms(self, user_id: uuid.UUID, terms_id: uuid.UUID) -> UserTermsAcceptanceRead:
        existing = self.repository.get_by_user_and_terms(user_id, terms_id)
        if existing:
            return UserTermsAcceptanceRead.model_validate(existing)

        data = UserTermsAcceptanceCreate(user_id=user_id, terms_id=terms_id)

        try:
            created = self.repository.create(data.model_dump())
            return UserTermsAcceptanceRead.model_validate(created)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    def get_by_id(self, acceptance_id: uuid.UUID) -> UserTermsAcceptanceRead:
        acc = self.repository.get_by_id(acceptance_id)
        if not acc:
            raise HTTPException(status_code=404, detail="Acceptance not found.")

        return UserTermsAcceptanceRead.model_validate(acc)

    def list_user_acceptances(self, user_id: uuid.UUID) -> List[UserTermsAcceptanceList]:
        acc_list = self.repository.list_by_user(user_id)
        return [UserTermsAcceptanceList.model_validate(a) for a in acc_list]

    def get_user_acceptance(
        self,
        user_id: uuid.UUID,
        terms_id: uuid.UUID,
    ) -> Optional[UserTermsAcceptanceRead]:
        acc = self.repository.get_by_user_and_terms(user_id, terms_id)
        return UserTermsAcceptanceRead.model_validate(acc) if acc else None

    def get_last_user_acceptance(self, user_id: uuid.UUID) -> Optional[UserTermsAcceptanceRead]:
        acc = self.repository.get_last_by_user(user_id)
        return UserTermsAcceptanceRead.model_validate(acc) if acc else None

    def has_user_accepted_terms(self, user_id: uuid.UUID, terms_id: uuid.UUID) -> bool:
        return self.repository.get_by_user_and_terms(user_id, terms_id) is not None
