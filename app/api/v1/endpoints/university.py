from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.domains.university.university_service import UniversityService
from app.schemas.university import UniversityRead, UniversitySimpleRead

router = APIRouter()


def get_university_service(db: Session = Depends(get_db)) -> UniversityService:
    """Dependency to inject HousingCategoryService."""
    return UniversityService(db)

@router.get("/", response_model=List[UniversityRead])
def get_universities(university_service: UniversityService = Depends(get_university_service)):
    """
    Gets a list of all universities and their faculties
    to populate the frontend dropdowns.
    """
    return university_service.get_all_with_faculties()

@router.get("/simple", response_model=List[UniversitySimpleRead])
def get_universities_simple(university_service: UniversityService = Depends(get_university_service)):
    """
    Returns universities without faculties.
    """
    return university_service.get_all_simple()
