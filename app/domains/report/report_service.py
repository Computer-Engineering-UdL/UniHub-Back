import datetime
import uuid
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.domains.report.report_repository import ReportRepository
from app.models.report import Report
from app.schemas.report import (
    BulkActionPayload,
    BulkActionResponse,
    ReportCreate,
    ReportStats,
    ReportUpdate,
)


class ReportService:
    """Service layer for report business logic."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = ReportRepository(db)

    def create_report(self, report_in: ReportCreate, reporter_id: uuid.UUID) -> Report:
        """Create a new report."""
        try:
            report_data = report_in.model_dump()
            report_data["reported_by_id"] = reporter_id

            return self.repository.create(report_data)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to create report: {str(e)}")

    def get_report(self, report_id: uuid.UUID) -> Report:
        """Get a single report by ID."""
        report = self.repository.get_by_id(report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        return report

    def get_reports(
        self,
        page: int = 1,
        size: int = 20,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        category: Optional[str] = None,
        reason: Optional[str] = None,
        search: Optional[str] = None,
    ) -> dict:
        """Get paginated list of reports with filters."""
        skip = (page - 1) * size
        reports, total = self.repository.get_paginated(
            skip=skip,
            limit=size,
            status=status,
            priority=priority,
            category=category,
            reason=reason,
            search=search,
        )

        return {"reports": reports, "total": total}

    def get_my_reports(self, user_id: uuid.UUID, page: int = 1, size: int = 20) -> dict:
        """Get reports created by a specific user."""
        skip = (page - 1) * size
        reports, total = self.repository.get_by_reporter(user_id=user_id, skip=skip, limit=size)

        return {"reports": reports, "total": total}

    def update_report(self, report_id: uuid.UUID, update_data: ReportUpdate, reviewer_id: uuid.UUID) -> Report:
        """Update a report."""
        report = self.repository.get_by_id(report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        update_dict = update_data.model_dump(exclude_unset=True)

        if update_dict:
            update_dict["reviewed_by_id"] = reviewer_id
            update_dict["reviewed_at"] = datetime.datetime.now(datetime.UTC)

        return self.repository.update(report, update_dict)

    def delete_report(self, report_id: uuid.UUID) -> dict:
        """Delete a report."""
        report = self.repository.get_by_id(report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        self.repository.delete(report)
        return {"success": True, "message": "Report deleted"}

    def get_stats(self) -> ReportStats:
        """Get report statistics for dashboard."""
        stats_data = self.repository.get_stats()
        return ReportStats(**stats_data)

    def bulk_update_reports(self, payload: BulkActionPayload, reviewer_id: uuid.UUID) -> BulkActionResponse:
        """Apply bulk action to multiple reports."""
        update_dict = payload.action.model_dump(exclude_unset=True)

        if update_dict:
            update_dict["reviewed_by_id"] = reviewer_id
            update_dict["reviewed_at"] = datetime.datetime.now(datetime.UTC)

        count = self.repository.bulk_update(payload.report_ids, update_dict)

        return BulkActionResponse(updated=count, message=f"{count} reports updated successfully")
