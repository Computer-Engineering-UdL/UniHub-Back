from typing import List

from sqlalchemy.orm import Session

from app.domains.university.university_repository import UniversityRepository
from app.schemas.university import UniversityRead


class UniversityService:
    """Service layer for university-related business logic."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = UniversityRepository(db)

    def get_all_with_faculties(self) -> List[UniversityRead]:
        """Get all universities with their faculties."""
        universities = self.repository.get_all_with_faculties()
        return [UniversityRead.model_validate(uni) for uni in universities]
