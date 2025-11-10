from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.crud.university import UniversityCRUD
from app.schemas.university import UniversityRead

router = APIRouter()


@router.get("/", response_model=List[UniversityRead])
def get_universities(db: Session = Depends(get_db)):
    """
    Gets a list of all universities and their faculties
    to populate the frontend dropdowns.
    """
    return UniversityCRUD.get_all_with_faculties(db)
