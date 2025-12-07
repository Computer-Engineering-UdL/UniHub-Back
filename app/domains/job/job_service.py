import uuid
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.domains.file.file_association_service import FileAssociationService
from app.domains.job.job_repository import JobRepository
from app.literals.job import JobCategory, JobType
from app.literals.users import Role
from app.models.job import JobOfferTableModel
from app.models.user import User
from app.schemas.job import JobOfferCreate, JobOfferRead, JobOfferUpdate


class JobService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = JobRepository(db)
        self.file_assoc_service = FileAssociationService(db)

    def _enrich_job_read(self, job: JobOfferTableModel, current_user: Optional[User] = None) -> JobOfferRead:
        logo_url = job.logo
        is_saved = False
        is_applied = False

        if current_user:
            is_saved = self.repo.is_saved(current_user.id, job.id)
            is_applied = self.repo.has_applied(current_user.id, job.id)

        return JobOfferRead(
            **job.__dict__,
            logo_url=logo_url,
            application_count=len(job.applications) if job.applications else 0,
            is_saved=is_saved,
            is_applied=is_applied,
        )

    def create_offer(self, user: User, offer_in: JobOfferCreate) -> JobOfferRead:
        if user.role != Role.RECRUITER and user.role != Role.ADMIN:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only recruiters can post job offers.")

        job_data = offer_in.model_dump(exclude={"file_ids"})
        new_job = JobOfferTableModel(**job_data, user_id=user.id)

        created_job = self.repo.create(new_job)

        if offer_in.file_ids:
            self.file_assoc_service.create_associations(
                file_ids=offer_in.file_ids, entity_id=created_job.id, entity_type="job_offer", category="logo"
            )
            self.db.refresh(created_job)

        return self._enrich_job_read(created_job, user)

    def list_offers(
        self,
        user: Optional[User] = None,
        category: Optional[JobCategory] = None,
        job_type: Optional[JobType] = None,
        search: Optional[str] = None,
    ) -> List[JobOfferRead]:
        jobs = self.repo.get_all(category=category, job_type=job_type, search=search)
        return [self._enrich_job_read(job, user) for job in jobs]

    def get_offer(self, job_id: uuid.UUID, user: Optional[User] = None) -> JobOfferRead:
        job = self.repo.get_by_id(job_id)
        if not job:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job offer not found")
        return self._enrich_job_read(job, user)

    def delete_offer(self, job_id: uuid.UUID, user: User):
        job = self.repo.get_by_id(job_id)
        if not job:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job offer not found")

        if user.role != Role.ADMIN and job.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this offer")

        self.repo.delete(job)

    def update_offer(self, job_id: uuid.UUID, user: User, update_in: JobOfferUpdate) -> JobOfferRead:
        job = self.repo.get_by_id(job_id)
        if not job:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job offer not found")
        if user.role != Role.ADMIN and job.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to edit this offer")

        update_data = update_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(job, field):
                setattr(job, field, value)

        updated_job = self.repo.update(job)
        return self._enrich_job_read(updated_job, user)

    def apply_to_job(self, job_id: uuid.UUID, user: User):
        if user.role != Role.BASIC:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only basic users can apply to jobs.")

        job = self.repo.get_by_id(job_id)
        if not job:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

        if self.repo.has_applied(user.id, job_id):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You have already applied to this job.")

        self.repo.add_application(user.id, job_id)
        return {"message": "Application submitted successfully"}

    def toggle_save_job(self, job_id: uuid.UUID, user: User):
        job = self.repo.get_by_id(job_id)
        if not job:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

        if self.repo.is_saved(user.id, job_id):
            self.repo.unsave_job(user.id, job_id)
            return {"message": "Job removed from saved", "is_saved": False}
        else:
            self.repo.save_job(user.id, job_id)
            return {"message": "Job saved", "is_saved": True}

    def get_my_applications(self, user: User) -> List[JobOfferRead]:
        jobs = self.repo.get_applied_jobs(user.id)
        return [self._enrich_job_read(job, user) for job in jobs]

    def get_my_saved_jobs(self, user: User) -> List[JobOfferRead]:
        jobs = self.repo.get_saved_jobs(user.id)
        return [self._enrich_job_read(job, user) for job in jobs]
