from typing import List, Optional
from uuid import UUID

from app.literals.job import JobCategory, JobType, JobWorkplace


def sample_job_payload(
    title: str = "Senior Backend Developer",
    description: str = "We are looking for a Python expert with FastAPI experience.",
    category: str = JobCategory.TECHNOLOGY.value,
    job_type: str = JobType.FULL_TIME.value,
    workplace_type: str = JobWorkplace.REMOTE.value,
    location: str = "Madrid",
    salary_min: float = 40000.0,
    salary_max: float = 60000.0,
    company_name: str = "TechStartup BCN",
    company_description: str = "Leading tech company.",
    company_website: str = "https://example.com",
    company_employee_count: str = "50-100",
    file_ids: Optional[List[UUID]] = None,
) -> dict:
    """
    Generate a sample job offer payload for testing.
    """
    payload = {
        "title": title,
        "description": description,
        "category": category,
        "job_type": job_type,
        "workplace_type": workplace_type,
        "location": location,
        "salary_min": salary_min,
        "salary_max": salary_max,
        "salary_period": "year",
        "company_name": company_name,
        "company_description": company_description,
        "company_website": company_website,
        "company_employee_count": company_employee_count,
        "file_ids": [str(fid) for fid in file_ids] if file_ids else [],
    }
    return payload
