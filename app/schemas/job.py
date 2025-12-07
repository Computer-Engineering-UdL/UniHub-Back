from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel

from app.literals.job import JobCategory, JobType, JobWorkplace


class JobOfferBase(BaseModel):
    title: str
    description: str
    category: JobCategory
    job_type: JobType
    workplace_type: JobWorkplace = JobWorkplace.ON_SITE
    location: str
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_period: str = "year"
    company_name: str
    company_description: Optional[str] = None
    company_website: Optional[str] = None
    company_employee_count: Optional[str] = None


class JobOfferCreate(JobOfferBase):
    file_ids: List[UUID] = []


class JobOfferUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[JobCategory] = None
    job_type: Optional[JobType] = None
    location: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    is_active: Optional[bool] = None
    company_name: Optional[str] = None


class JobApplicationRead(BaseModel):
    user_id: UUID
    applied_at: datetime


class JobOfferRead(JobOfferBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    is_active: bool
    logo_url: Optional[str] = None
    application_count: int = 0
    is_saved: bool = False
    is_applied: bool = False

    class Config:
        from_attributes = True


class JobOfferDetail(JobOfferRead):
    pass
