import uuid

from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from app.models import File
from app.schemas import FileUploadRequest


class FileCRUD:
    @staticmethod
    def create_file(db: Session, file_data: FileUploadRequest) -> File:
        """Create a new file record."""
        db_file = File(**file_data.model_dump())
        db.add(db_file)
        db.commit()
        db.refresh(db_file)
        return db_file

    @staticmethod
    def get_file_by_id(db: Session, file_id: uuid.UUID) -> File:
        """Retrieve a file by its ID if not deleted."""
        file_db = db.query(File).filter(File.id == file_id).one_or_none()
        if file_db is None or file_db.deleted:
            raise NoResultFound("File not found")
        return file_db

    @staticmethod
    def delete_file(db: Session, file_id: uuid.UUID):
        """Soft delete a file by marking it as deleted."""
        file_db = db.query(File).filter(File.id == file_id).one_or_none()
        if file_db is None or file_db.deleted:
            raise NoResultFound("File not found")
        file_db.deleted = True
        db.commit()
        return True

    @staticmethod
    def list_files(db: Session, skip: int = 0, limit: int = 100) -> list[File]:
        """List all active (non-deleted) files."""
        return db.query(File).filter(File.deleted.is_(False)).offset(skip).limit(limit).all()

    @staticmethod
    def list_files_by_user(db: Session, user_id: uuid.UUID, skip: int = 0, limit: int = 100) -> list[File]:
        """List all active files uploaded by a specific user."""
        return (
            db.query(File).filter(File.uploader_id == user_id, File.deleted.is_(False)).offset(skip).limit(limit).all()
        )

    @staticmethod
    def get_public_file(db: Session, file_id: uuid.UUID) -> File:
        """Retrieve a public file by its ID if not deleted."""
        file_db = (
            db.query(File).filter(File.id == file_id, File.is_public.is_(True), File.deleted.is_(False)).one_or_none()
        )
        if file_db is None:
            raise NoResultFound("Public file not found")
        return file_db

    @staticmethod
    def update_file_visibility(db: Session, file_id: uuid.UUID, is_public: bool):
        """Update the public visibility of a file."""
        file_db = db.query(File).filter(File.id == file_id).one_or_none()
        if file_db is None or file_db.deleted:
            raise NoResultFound("File not found")
        file_db.is_public = is_public
        db.commit()
        db.refresh(file_db)
        return file_db
