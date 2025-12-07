from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TermsBase(BaseModel):
    """Shared fields for create/update."""

    version: str = Field(
        min_length=1,
        max_length=20,
        description="Version identifier of the terms (e.g. 'v1.0')."
    )
    content: str = Field(
        description="Full text content of the terms."
    )

class TermsCreate(TermsBase):
    """Schema for creating new terms."""
    pass

class TermsUpdate(BaseModel):
    """Schema for updating terms. All fields optional."""

    version: str | None = Field(
        None,
        min_length=1,
        max_length=20
    )
    content: str | None = None

    model_config = ConfigDict(from_attributes=True)

class TermsRead(TermsBase):
    """Schema for reading full terms entry."""

    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class TermsList(BaseModel):
    """Lightweight list-entry schema."""

    id: UUID
    version: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class TermsDetail(TermsRead):
    """Detailed schema including future related objects."""
    # e.g. accepted_by: List["UserTermsAcceptanceRead"]

    model_config = ConfigDict(from_attributes=True)

__all__ = [
    "TermsBase",
    "TermsCreate",
    "TermsUpdate",
    "TermsRead",
    "TermsList",
    "TermsDetail"
]
