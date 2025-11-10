from sqlalchemy.orm import Session, selectinload

from app.models.university import University


class UniversityCRUD:
    @staticmethod
    def get_all_with_faculties(db: Session):
        return db.query(University).options(selectinload(University.faculties)).all()
