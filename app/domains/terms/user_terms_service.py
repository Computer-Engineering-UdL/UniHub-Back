import uuid
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.domains.terms.terms_service import TermsService
from app.domains.terms.user_terms_repository import UserTermsAcceptanceRepository
from app.schemas.user_terms_acceptance import (
    UserTermsAcceptanceCreate,
    UserTermsAcceptanceList,
    UserTermsAcceptanceRead,
)


class UserTermsAcceptanceService:
    """Service layer for user–terms acceptance logic (latest Terms only)."""

    def __init__(self, db: Session, terms_service: TermsService):
        self.db = db
        self.repository = UserTermsAcceptanceRepository(db)
        self.terms_service = terms_service

    def accept_latest_terms(self, user_id: uuid.UUID) -> UserTermsAcceptanceRead:
        latest_terms = self.terms_service.get_latest_terms()
        if not latest_terms:
            raise HTTPException(status_code=404, detail="No Terms available to accept.")

        existing = self.repository.get_by_user_and_terms(user_id, latest_terms.id)
        if existing:
            return UserTermsAcceptanceRead.model_validate(existing)

        data = UserTermsAcceptanceCreate(user_id=user_id, terms_id=latest_terms.id)
        try:
            created = self.repository.create(data.model_dump())
            return UserTermsAcceptanceRead.model_validate(created)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    def get_last_user_acceptance(self, user_id: uuid.UUID) -> Optional[UserTermsAcceptanceRead]:
        acc = self.repository.get_last_by_user(user_id)
        return UserTermsAcceptanceRead.model_validate(acc) if acc else None

    def list_user_acceptances(self, user_id: uuid.UUID) -> List[UserTermsAcceptanceList]:
        acc_list = self.repository.list_by_user(user_id)
        return [UserTermsAcceptanceList.model_validate(a) for a in acc_list]
