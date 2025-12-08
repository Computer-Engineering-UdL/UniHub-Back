from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UserTermsAcceptanceBase(BaseModel):
    """Shared fields for create/update."""

    user_id: UUID
    terms_id: UUID

class UserTermsAcceptanceCreate(UserTermsAcceptanceBase):
    """Schema for creating a new acceptance record."""

    pass

class UserTermsAcceptanceRead(UserTermsAcceptanceBase):
    """Full schema for reading acceptance."""

    id: UUID
    version: str
    accepted_at: datetime

    model_config = ConfigDict(from_attributes=True)

class UserTermsAcceptanceList(BaseModel):
    """Lightweight list schema for acceptances."""

    id: UUID
    terms_id: UUID
    accepted_at: datetime
    version: str

    model_config = ConfigDict(from_attributes=True)


__all__ = [
    "UserTermsAcceptanceBase",
    "UserTermsAcceptanceCreate",
    "UserTermsAcceptanceRead",
    "UserTermsAcceptanceList",
]