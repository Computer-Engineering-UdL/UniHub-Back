from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.literals.report import ReportCategory, ReportPriority, ReportReason, ReportStatus


def to_camel(string: str) -> str:
    """Convert snake_case to camelCase."""
    components = string.split("_")
    return components[0] + "".join(word.capitalize() for word in components[1:])


class UserSummary(BaseModel):
    """Lightweight user info for report responses."""

    id: UUID
    username: str
    full_name: str
    avatar_url: Optional[str] = None

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True,
    )

    @model_validator(mode="before")
    @classmethod
    def compute_full_name(cls, data: Any) -> Any:
        """Compute full_name from first_name and last_name if not provided."""
        if hasattr(data, "first_name") and hasattr(data, "last_name"):
            if not hasattr(data, "full_name"):
                return {
                    "id": data.id,
                    "username": data.username,
                    "full_name": f"{data.first_name} {data.last_name}",
                    "avatar_url": getattr(data, "avatar_url", None),
                }
        return data


class ReportBase(BaseModel):
    """Base schema for report."""

    content_type: ReportCategory
    content_id: str
    reported_user_id: UUID
    reason: ReportReason
    description: Optional[str] = None

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


class ReportCreate(ReportBase):
    """Schema for creating a new report."""

    content_title: Optional[str] = None

    pass


class ReportUpdate(BaseModel):
    """Schema for updating a report (admin only)."""

    status: Optional[ReportStatus] = None
    priority: Optional[ReportPriority] = None
    resolution: Optional[str] = None

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


class ReportRead(BaseModel):
    """Full report schema for reading."""

    id: UUID
    reported_by: UserSummary
    reported_user: UserSummary
    content_type: str
    content_id: str
    content_title: Optional[str] = None
    reason: str
    description: Optional[str] = None
    status: str
    priority: str
    created_at: datetime
    updated_at: datetime
    reviewed_by: Optional[UserSummary] = None
    reviewed_at: Optional[datetime] = None
    resolution: Optional[str] = None

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True,
    )

    @model_validator(mode="before")
    @classmethod
    def map_relationships(cls, data: Any) -> Any:
        """Map ORM relationship names to schema field names."""
        if hasattr(data, "reported_by_user"):
            return {
                "id": data.id,
                "reported_by": data.reported_by_user,
                "reported_user": data.reported_user,
                "content_type": data.content_type,
                "content_id": data.content_id,
                "content_title": data.content_title,
                "reason": data.reason,
                "description": data.description,
                "status": data.status,
                "priority": data.priority,
                "created_at": data.created_at,
                "updated_at": data.updated_at,
                "reviewed_by": data.reviewed_by_user if data.reviewed_by_user else None,
                "reviewed_at": data.reviewed_at,
                "resolution": data.resolution,
            }
        return data


class ReportListResponse(BaseModel):
    """Response schema for paginated report list."""

    reports: list[ReportRead]
    total: int

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


class ReportStats(BaseModel):
    """Statistics for reports dashboard."""

    total: int = 0
    pending: int = 0
    reviewing: int = 0
    resolved: int = 0
    dismissed: int = 0
    critical: int = 0

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


class BulkActionPayload(BaseModel):
    """Schema for bulk report actions."""

    report_ids: list[UUID] = Field(..., min_length=1)
    action: ReportUpdate

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


class BulkActionResponse(BaseModel):
    """Response schema for bulk actions."""

    updated: int
    message: str

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


__all__ = [
    "UserSummary",
    "ReportBase",
    "ReportCreate",
    "ReportUpdate",
    "ReportRead",
    "ReportListResponse",
    "ReportStats",
    "BulkActionPayload",
    "BulkActionResponse",
]
