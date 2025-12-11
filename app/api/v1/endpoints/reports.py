from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.core.types import TokenData
from app.domains.report.report_service import ReportService
from app.schemas.report import ReportCreate, ReportListResponse, ReportRead

router = APIRouter()


def get_report_service(db: Session = Depends(get_db)) -> ReportService:
    """Dependency to inject ReportService."""
    return ReportService(db)


@router.post(
    "/",
    response_model=ReportRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new report",
    response_description="Returns the created report.",
)
def create_report(
    report_in: ReportCreate,
    service: ReportService = Depends(get_report_service),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Create a new report for content moderation.
    """
    return service.create_report(report_in, current_user.id)


@router.get(
    "/my",
    response_model=ReportListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get my reports",
    response_description="Returns paginated list of reports created by current user.",
)
def get_my_reports(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    service: ReportService = Depends(get_report_service),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Get all reports created by the authenticated user.
    """
    return service.get_my_reports(current_user.id, page, size)
