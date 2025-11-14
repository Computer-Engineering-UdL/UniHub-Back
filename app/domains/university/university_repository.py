from typing import List

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.university import University
from app.repositories.base import BaseRepository


class UniversityRepository(BaseRepository[University]):
    """Repository for University entity with specialized queries."""

    def __init__(self, db: Session):
        super().__init__(University, db)
        self.model = self.model_class

    def get_all_with_faculties(self) -> List[University]:
        """Retrieve all universities with their faculties loaded."""
        stmt = select(University).options(selectinload(University.faculties))
        return list(self.db.scalars(stmt).all())
