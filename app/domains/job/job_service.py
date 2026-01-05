import uuid
from typing import List, Optional

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.domains.file.file_association_service import FileAssociationService
from app.domains.file.file_service import FileService
from app.domains.job.job_repository import JobRepository
from app.literals.job import JobCategory, JobType
from app.literals.users import Role
from app.models.job import JobOfferTableModel
from app.models.user import User
from app.schemas import FileAssociationCreate
from app.schemas.job import JobApplicationCreate, JobApplicationRead, JobOfferCreate, JobOfferRead, JobOfferUpdate


class JobService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = JobRepository(db)
        self.file_assoc_service = FileAssociationService(db)
        self.file_service = FileService(db)

    def _enrich_job_read(self, job: JobOfferTableModel, current_user: Optional[User] = None) -> JobOfferRead:
        logo_url = None
        if job.file_associations:
            file_id = job.file_associations[0].file_id
            logo_url = f"{settings.API_VERSION}/files/public/{file_id}"
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
            associations = [
                FileAssociationCreate(
                    file_id=file_id, entity_type="job_offer", entity_id=created_job.id, category="logo", order=0
                )
                for file_id in offer_in.file_ids
            ]
            self.file_assoc_service.create_associations_bulk(associations=associations, current_user=user)
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

    async def apply_to_job(
        self, job_id: uuid.UUID, user: User, application_in: JobApplicationCreate, cv_file: UploadFile
    ):
        if user.role != Role.BASIC and user.role != Role.ADMIN:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only basic users can apply to jobs.")

        job = self.repo.get_by_id(job_id)
        if not job:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

        if self.repo.has_applied(user.id, job_id):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You have already applied to this job.")

        allowed_types = [
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ]

        if cv_file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file format. Only PDF, DOC and DOCX are allowed.",
            )

        uploaded_file = await self.file_service.upload_file(file=cv_file, is_public=False, current_user=user)
        self.repo.add_application(
            user.id,
            job_id,
            uploaded_file.id,
            full_name=application_in.full_name,
            email=application_in.email,
            phone=application_in.phone,
            cover_letter=application_in.cover_letter,
        )
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

    def get_job_applications(self, job_id: uuid.UUID, current_user: User) -> List[JobApplicationRead]:
        job = self.repo.get_by_id(job_id)
        if not job:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job offer not found")

        if job.user_id != current_user.id and current_user.role != Role.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to view applications for this job"
            )

        applications = job.applications
        results = []

        for app in applications:
            cv_link = None
            if app.cv_file_id:
                cv_link = f"{settings.API_VERSION}/files/public/{app.cv_file_id}"
            results.append(
                JobApplicationRead(
                    id=app.id,
                    user_id=app.user_id,
                    job_offer_id=app.job_id,
                    full_name=app.full_name,
                    email=app.email,
                    phone=app.phone,
                    cover_letter=app.cover_letter,
                    applied_at=app.applied_at,
                    cv_url=cv_link,
                )
            )
        return results
