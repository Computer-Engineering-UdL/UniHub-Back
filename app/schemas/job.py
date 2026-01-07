from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr

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


class JobApplicationCreate(BaseModel):
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    cover_letter: Optional[str] = None


class JobApplicationRead(BaseModel):
    id: UUID
    user_id: UUID
    job_offer_id: UUID
    full_name: str
    email: str
    phone: Optional[str] = None
    cover_letter: Optional[str] = None
    cv_url: Optional[str] = None
    applied_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobOfferRead(JobOfferBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    is_active: bool
    logo_url: Optional[str] = None
    application_count: int = 0
    is_saved: bool = False
    is_applied: bool = False

    model_config = ConfigDict(from_attributes=True)


class PagedJobOffersResult(BaseModel):
    items: List[JobOfferRead]
    total: int
    page: int
    size: int
    pages: int


class JobOfferDetail(JobOfferRead):
    pass
