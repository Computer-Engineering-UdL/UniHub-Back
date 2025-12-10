import uuid
from typing import Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import require_role
from app.core.database import get_db
from app.core.types import TokenData
from app.domains.report.report_service import ReportService
from app.literals.users import Role
from app.schemas.report import (
    BulkActionPayload,
    BulkActionResponse,
    ReportListResponse,
    ReportRead,
    ReportStats,
    ReportUpdate,
)

router = APIRouter()


def get_report_service(db: Session = Depends(get_db)) -> ReportService:
    """Dependency to inject ReportService."""
    return ReportService(db)


@router.get(
    "/stats",
    response_model=ReportStats,
    status_code=status.HTTP_200_OK,
    summary="Get report statistics",
    response_description="Returns dashboard statistics for reports.",
)
def get_report_stats(
    service: ReportService = Depends(get_report_service),
    _: TokenData = Depends(require_role(Role.ADMIN)),
):
    """
    Get report statistics for admin dashboard.
    """
    return service.get_stats()


@router.get(
    "/",
    response_model=ReportListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get all reports with filters",
    response_description="Returns paginated and filtered list of reports.",
)
def get_reports(
    page: int = 1,
    size: int = 20,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    category: Optional[str] = None,
    reason: Optional[str] = None,
    search: Optional[str] = None,
    service: ReportService = Depends(get_report_service),
    _: TokenData = Depends(require_role(Role.ADMIN)),
):
    """
    Get paginated list of reports with optional filters.
    """
    return service.get_reports(
        page=page,
        size=size,
        status=status,
        priority=priority,
        category=category,
        reason=reason,
        search=search,
    )


################################################
# /bulk must be defined BEFORE /{report_id}!!! #
################################################


@router.patch(
    "/bulk",
    response_model=BulkActionResponse,
    status_code=status.HTTP_200_OK,
    summary="Bulk update reports",
    response_description="Returns count of updated reports.",
)
def bulk_update_reports(
    payload: BulkActionPayload,
    service: ReportService = Depends(get_report_service),
    current_user: TokenData = Depends(require_role(Role.ADMIN)),
):
    """
    Apply the same action to multiple reports.
    """
    return service.bulk_update_reports(payload, current_user.id)


@router.get(
    "/{report_id}",
    response_model=ReportRead,
    status_code=status.HTTP_200_OK,
    summary="Get report details",
    response_description="Returns full report details.",
)
def get_report(
    report_id: uuid.UUID,
    service: ReportService = Depends(get_report_service),
    _: TokenData = Depends(require_role(Role.ADMIN)),
):
    """
    Get detailed information about a specific report.
    """
    return service.get_report(report_id)


@router.patch(
    "/{report_id}",
    response_model=ReportRead,
    status_code=status.HTTP_200_OK,
    summary="Update a report",
    response_description="Returns updated report.",
)
def update_report(
    report_id: uuid.UUID,
    update_data: ReportUpdate,
    service: ReportService = Depends(get_report_service),
    current_user: TokenData = Depends(require_role(Role.ADMIN)),
):
    """
    Update report status, priority, or resolution.
    """
    return service.update_report(report_id, update_data, current_user.id)


@router.delete(
    "/{report_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a report",
    response_description="Returns success message.",
)
def delete_report(
    report_id: uuid.UUID,
    service: ReportService = Depends(get_report_service),
    _: TokenData = Depends(require_role(Role.ADMIN)),
):
    """
    Permanently delete a report.
    """
    return service.delete_report(report_id)
