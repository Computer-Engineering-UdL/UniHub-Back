import uuid
from typing import List, Optional, Tuple

from sqlalchemy import and_, desc, func, select
from sqlalchemy.orm import Session, selectinload

from app.literals.job import JobCategory, JobType
from app.models.job import JobApplication, JobOfferTableModel, SavedJob


class JobRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, job: JobOfferTableModel) -> JobOfferTableModel:
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def get_by_id(self, job_id: uuid.UUID) -> Optional[JobOfferTableModel]:
        stmt = (
            select(JobOfferTableModel)
            .where(JobOfferTableModel.id == job_id)
            .options(selectinload(JobOfferTableModel.file_associations), selectinload(JobOfferTableModel.applications))
        )
        return self.db.scalar(stmt)

    def get_all(
        self,
        skip: int = 0,
        limit: int = 20,
        category: Optional[JobCategory] = None,
        job_type: Optional[JobType] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[JobOfferTableModel], int]:
        stmt = select(JobOfferTableModel).where(JobOfferTableModel.is_active.is_(True))

        if category:
            stmt = stmt.where(JobOfferTableModel.category == category)
        if job_type:
            stmt = stmt.where(JobOfferTableModel.job_type == job_type)
        if search:
            stmt = stmt.where(JobOfferTableModel.title.ilike(f"%{search}%"))
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.scalar(count_stmt) or 0
        stmt = stmt.order_by(desc(JobOfferTableModel.created_at)).offset(skip).limit(limit)
        stmt = stmt.options(selectinload(JobOfferTableModel.file_associations))
        items = list(self.db.scalars(stmt).all())
        return items, total

    def update(self, job: JobOfferTableModel) -> JobOfferTableModel:
        self.db.commit()
        self.db.refresh(job)
        return job

    def delete(self, job: JobOfferTableModel) -> None:
        self.db.delete(job)
        self.db.commit()

    # --- APPS & SAVES ---
    def add_application(
        self,
        user_id: uuid.UUID,
        job_id: uuid.UUID,
        cv_file_id: uuid.UUID,
        full_name: str,
        email: str,
        phone: Optional[str] = None,
        cover_letter: Optional[str] = None,
    ):
        app = JobApplication(
            user_id=user_id,
            job_id=job_id,
            cv_file_id=cv_file_id,
            full_name=full_name,
            email=email,
            phone=phone,
            cover_letter=cover_letter,
        )
        self.db.add(app)
        self.db.commit()

    def has_applied(self, user_id: uuid.UUID, job_id: uuid.UUID) -> bool:
        stmt = select(JobApplication).where(and_(JobApplication.user_id == user_id, JobApplication.job_id == job_id))
        return self.db.scalar(stmt) is not None

    def save_job(self, user_id: uuid.UUID, job_id: uuid.UUID):
        saved = SavedJob(user_id=user_id, job_id=job_id)
        self.db.add(saved)
        self.db.commit()

    def unsave_job(self, user_id: uuid.UUID, job_id: uuid.UUID):
        stmt = select(SavedJob).where(and_(SavedJob.user_id == user_id, SavedJob.job_id == job_id))
        saved = self.db.scalar(stmt)
        if saved:
            self.db.delete(saved)
            self.db.commit()

    def is_saved(self, user_id: uuid.UUID, job_id: uuid.UUID) -> bool:
        stmt = select(SavedJob).where(and_(SavedJob.user_id == user_id, SavedJob.job_id == job_id))
        return self.db.scalar(stmt) is not None

    def get_saved_jobs(self, user_id: uuid.UUID) -> List[JobOfferTableModel]:
        stmt = select(JobOfferTableModel).join(SavedJob).where(SavedJob.user_id == user_id)
        return list(self.db.scalars(stmt).all())

    def get_applied_jobs(self, user_id: uuid.UUID) -> List[JobOfferTableModel]:
        stmt = select(JobOfferTableModel).join(JobApplication).where(JobApplication.user_id == user_id)
        return list(self.db.scalars(stmt).all())
