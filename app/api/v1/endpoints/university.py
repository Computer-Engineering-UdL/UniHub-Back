from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.domains.university.university_service import UniversityService
from app.schemas.university import UniversityRead

router = APIRouter()


def get_university_service(db: Session = Depends(get_db)) -> UniversityService:
    """Dependency to inject HousingCategoryService."""
    return UniversityService(db)


@router.get("/", response_model=List[UniversityRead])
def get_universities(university_service=Depends(get_university_service)):
    """
    Gets a list of all universities and their faculties
    to populate the frontend dropdowns.
    """
    return get_university_service.get_all_with_faculties()
