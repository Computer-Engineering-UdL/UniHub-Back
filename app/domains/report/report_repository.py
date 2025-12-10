import uuid
from typing import List, Optional

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.literals.report import ReportPriority, ReportStatus
from app.models.report import Report
from app.repositories.base import BaseRepository


class ReportRepository(BaseRepository[Report]):
    """Repository for Report entity."""

    def __init__(self, db: Session):
        super().__init__(Report, db)
        self.model = self.model_class

    def create(self, report_data: dict) -> Report:
        """Create a new report."""
        report = Report(**report_data)
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report

    def get_by_id(self, report_id: uuid.UUID) -> Optional[Report]:
        """Get report by ID with all relationships loaded."""
        stmt = select(Report).filter(Report.id == report_id)
        return self.db.scalars(stmt).first()

    def get_paginated(
        self,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        category: Optional[str] = None,
        reason: Optional[str] = None,
        search: Optional[str] = None,
    ) -> tuple[List[Report], int]:
        """
        Get paginated list of reports with filters.
        """
        stmt = select(Report)

        if status:
            stmt = stmt.filter(Report.status == status)
        if priority:
            stmt = stmt.filter(Report.priority == priority)
        if category:
            stmt = stmt.filter(Report.content_type == category)
        if reason:
            stmt = stmt.filter(Report.reason == reason)
        if search:
            stmt = stmt.filter(
                or_(
                    Report.content_title.ilike(f"%{search}%"),
                    Report.description.ilike(f"%{search}%"),
                    Report.content_id.ilike(f"%{search}%"),
                )
            )

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.scalar(count_stmt) or 0

        stmt = stmt.order_by(Report.created_at.desc()).offset(skip).limit(limit)
        reports = list(self.db.scalars(stmt).all())

        return reports, total

    def get_by_reporter(self, user_id: uuid.UUID, skip: int = 0, limit: int = 20) -> tuple[List[Report], int]:
        """Get reports created by a specific user."""
        stmt = select(Report).filter(Report.reported_by_id == user_id)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.scalar(count_stmt) or 0

        stmt = stmt.order_by(Report.created_at.desc()).offset(skip).limit(limit)
        reports = list(self.db.scalars(stmt).all())

        return reports, total

    def update(self, report: Report, update_data: dict) -> Report:
        """Update a report."""
        for key, value in update_data.items():
            if value is not None and hasattr(report, key):
                setattr(report, key, value)

        self.db.commit()
        self.db.refresh(report)
        return report

    def delete(self, report: Report) -> None:
        """Delete a report."""
        self.db.delete(report)
        self.db.commit()

    def get_stats(self) -> dict:
        """Get report statistics."""

        status_stmt = select(Report.status, func.count(Report.id)).group_by(Report.status)
        status_counts = {status: count for status, count in self.db.execute(status_stmt)}

        critical_count = (
            self.db.scalar(select(func.count(Report.id)).filter(Report.priority == ReportPriority.CRITICAL.value)) or 0
        )

        return {
            "total": sum(status_counts.values()),
            "pending": status_counts.get(ReportStatus.PENDING.value, 0),
            "reviewing": status_counts.get(ReportStatus.REVIEWING.value, 0),
            "resolved": status_counts.get(ReportStatus.RESOLVED.value, 0),
            "dismissed": status_counts.get(ReportStatus.DISMISSED.value, 0),
            "critical": critical_count,
        }

    def bulk_update(self, report_ids: List[uuid.UUID], update_data: dict) -> int:
        """Bulk update multiple reports. Returns count of updated reports."""
        stmt = select(Report).filter(Report.id.in_(report_ids))
        reports = list(self.db.scalars(stmt).all())

        for report in reports:
            for key, value in update_data.items():
                if value is not None and hasattr(report, key):
                    setattr(report, key, value)

        self.db.commit()
        return len(reports)
