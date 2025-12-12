from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import require_role
from app.core.database import get_db
from app.domains.dashboard.dashboard_service import DashboardService
from app.literals.dashboard import TimeRange
from app.literals.users import Role
from app.schemas.dashboard import (
    ActivityItem,
    ChartResponse,
    DashboardStatsResponse,
)

router = APIRouter()


@router.get("/stats", response_model=DashboardStatsResponse)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    _: dict = Depends(require_role(Role.ADMIN)),  # Solo Admins
):
    """
    Get KPI statistics for the admin dashboard.
    Returns total users, active content, engagement rates, etc.
    """
    service = DashboardService(db)
    return service.get_stats()


@router.get("/charts/distribution", response_model=ChartResponse)
def get_distribution_chart(
    db: Session = Depends(get_db),
    _: dict = Depends(require_role(Role.ADMIN)),
):
    """
    Get content distribution data for pie/doughnut charts.
    Shows the proportion of Housing vs other content.
    """
    service = DashboardService(db)
    return service.get_content_distribution()


@router.get("/charts/activity", response_model=ChartResponse)
def get_activity_chart(
    time_range: TimeRange = Query(TimeRange.WEEK, description="Range: week, month, trimester, year"),
    db: Session = Depends(get_db),
    _: dict = Depends(require_role(Role.ADMIN)),
):
    """Get activity data for charts with dynamic range."""
    service = DashboardService(db)
    return service.get_activity_chart(time_range)


@router.get("/charts/channels", response_model=ChartResponse)
def get_channels_chart(
    db: Session = Depends(get_db),
    _: dict = Depends(require_role(Role.ADMIN)),
):
    """Get channel distribution stats."""
    service = DashboardService(db)
    return service.get_channels_distribution()


@router.get("/activity", response_model=List[ActivityItem])
def get_recent_activity(
    db: Session = Depends(get_db),
    _: dict = Depends(require_role(Role.ADMIN)),
):
    """
    Get a timeline of recent system activity.
    Merges new user registrations and new housing offers.
    """
    service = DashboardService(db)
    return service.get_recent_activity()
