from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_optional_current_user, require_verified_email
from app.core.database import get_db
from app.domains.job.job_service import JobService
from app.literals.job import JobCategory, JobType
from app.models.user import User
from app.schemas.job import JobOfferCreate, JobOfferRead, JobOfferUpdate

router = APIRouter()


@router.post("/", response_model=JobOfferRead, status_code=201)
def create_job_offer(
    offer_in: JobOfferCreate,
    current_user: User = Depends(require_verified_email),
    db: Session = Depends(get_db),
):
    """(SELLER Only) Create a new job offer."""
    service = JobService(db)
    return service.create_offer(current_user, offer_in)


@router.get("/", response_model=List[JobOfferRead])
def list_job_offers(
    category: Optional[JobCategory] = None,
    job_type: Optional[JobType] = None,
    search: Optional[str] = None,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    """List all active job offers with filters."""
    service = JobService(db)
    return service.list_offers(current_user, category, job_type, search)


@router.get("/saved", response_model=List[JobOfferRead])
def list_my_saved_jobs(
    current_user: User = Depends(require_verified_email),
    db: Session = Depends(get_db),
):
    """List jobs saved by the current user."""
    service = JobService(db)
    return service.get_my_saved_jobs(current_user)


@router.get("/applied", response_model=List[JobOfferRead])
def list_my_applications(
    current_user: User = Depends(require_verified_email),
    db: Session = Depends(get_db),
):
    """List jobs the current user has applied to."""
    service = JobService(db)
    return service.get_my_applications(current_user)


@router.get("/{job_id}", response_model=JobOfferRead)
def get_job_offer(
    job_id: UUID,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    """Get details of a specific job offer."""
    service = JobService(db)
    return service.get_offer(job_id, current_user)


@router.patch("/{job_id}", response_model=JobOfferRead)
def update_job_offer(
    job_id: UUID,
    offer_update: JobOfferUpdate,
    current_user: User = Depends(require_verified_email),
    db: Session = Depends(get_db),
):
    """(SELLER/ADMIN) Update a job offer."""
    service = JobService(db)
    return service.update_offer(job_id, current_user, offer_update)


@router.delete("/{job_id}", status_code=204)
def delete_job_offer(
    job_id: UUID,
    current_user: User = Depends(require_verified_email),
    db: Session = Depends(get_db),
):
    """(SELLER/ADMIN) Delete a job offer."""
    service = JobService(db)
    service.delete_offer(job_id, current_user)


@router.post("/{job_id}/apply", status_code=200)
def apply_to_job(
    job_id: UUID,
    current_user: User = Depends(require_verified_email),
    db: Session = Depends(get_db),
):
    """(BASIC Only) Apply to a job."""
    service = JobService(db)
    return service.apply_to_job(job_id, current_user)


@router.post("/{job_id}/save", status_code=200)
def toggle_save_job(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Toggle save/unsave a job offer."""
    service = JobService(db)
    return service.toggle_save_job(job_id, current_user)
