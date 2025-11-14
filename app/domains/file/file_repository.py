import uuid
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from app.models import File
from app.repositories.base import BaseRepository


class FileRepository(BaseRepository[File]):
    """Repository for File entity with specialized queries."""

    def __init__(self, db: Session):
        super().__init__(File, db)
        self.model = self.model_class

    def create(self, file_data: dict) -> File:
        """Create a new file record."""
        file = File(**file_data)
        self.db.add(file)
        self.db.commit()
        self.db.refresh(file)
        return file

    def get_by_id(self, file_id: uuid.UUID) -> Optional[File]:
        """Retrieve a file by its ID if not deleted."""
        stmt = select(File).filter(File.id == file_id, File.deleted.is_(False))
        return self.db.scalar(stmt)

    def get_public_file(self, file_id: uuid.UUID) -> Optional[File]:
        """Retrieve a public file by its ID if not deleted."""
        stmt = select(File).filter(
            File.id == file_id,
            File.is_public,
            File.deleted.is_(False),
        )
        return self.db.scalar(stmt)

    def list_all(self, skip: int = 0, limit: int = 100) -> List[File]:
        """List all active (non-deleted) files."""
        stmt = select(File).filter(File.deleted.is_(False)).offset(skip).limit(limit)
        return list(self.db.scalars(stmt).all())

    def list_by_user(self, user_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[File]:
        """List all active files uploaded by a specific user."""
        stmt = select(File).filter(File.uploader_id == user_id, File.deleted.is_(False)).offset(skip).limit(limit)
        return list(self.db.scalars(stmt).all())

    def soft_delete(self, file_id: uuid.UUID) -> bool:
        """Soft delete a file by marking it as deleted."""
        file = self.get_by_id(file_id)
        if not file:
            raise NoResultFound("File not found")
        file.deleted = True
        self.db.commit()
        return True

    def update_visibility(self, file_id: uuid.UUID, is_public: bool) -> File:
        """Update the public visibility of a file."""
        file = self.get_by_id(file_id)
        if not file:
            raise NoResultFound("File not found")
        file.is_public = is_public
        self.db.commit()
        self.db.refresh(file)
        return file
