import uuid
from typing import List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.types import TokenData
from app.domains.file.file_association_repository import FileAssociationRepository
from app.domains.file.file_repository import FileRepository
from app.literals.users import Role
from app.schemas import (
    FileAssociationCreate,
    FileAssociationRead,
    FileAssociationReorder,
    FileAssociationUpdate,
    FileAssociationWithFile,
)


class FileAssociationService:
    """Service layer for file association-related business logic."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = FileAssociationRepository(db)
        self.file_repository = FileRepository(db)

    def create_association(
        self,
        association_in: FileAssociationCreate,
        current_user: TokenData,
    ) -> FileAssociationRead:
        """Create a new file association."""
        file_db = self.file_repository.get_by_id(association_in.file_id)
        if not file_db:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found",
            )

        if file_db.uploader_id != current_user.id and current_user.role != Role.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to use this file",
            )

        association_data = association_in.model_dump()
        association = self.repository.create(association_data)
        return FileAssociationRead.model_validate(association)

    def create_associations_bulk(
        self,
        associations: List[FileAssociationCreate],
        current_user: TokenData,
    ) -> List[FileAssociationRead]:
        """Create multiple file associations at once."""
        for assoc in associations:
            file_db = self.file_repository.get_by_id(assoc.file_id)
            if not file_db:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"File {assoc.file_id} not found",
                )

            if file_db.uploader_id != current_user.id and current_user.role != Role.ADMIN:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"You don't have permission to use file {assoc.file_id}",
                )

        associations_data = [assoc.model_dump() for assoc in associations]
        created_associations = self.repository.bulk_create(associations_data)
        return [FileAssociationRead.model_validate(assoc) for assoc in created_associations]

    def get_association(self, association_id: uuid.UUID) -> FileAssociationRead:
        """Get a specific file association by ID."""
        association = self.repository.get_by_id(association_id)
        if not association:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Association not found",
            )
        return FileAssociationRead.model_validate(association)

    def get_associations_by_entity(
        self,
        entity_type: str,
        entity_id: uuid.UUID,
        category: str = None,
    ) -> List[FileAssociationWithFile]:
        """Get all file associations for a specific entity."""
        associations = self.repository.get_by_entity(entity_type, entity_id, category)
        return [FileAssociationWithFile.model_validate(assoc) for assoc in associations]

    def update_association(
        self,
        association_id: uuid.UUID,
        update_data: FileAssociationUpdate,
        current_user: TokenData,
    ) -> FileAssociationRead:
        """Update file association metadata or order."""
        association = self.repository.get_by_id(association_id)
        if not association:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Association not found",
            )

        file_db = self.file_repository.get_by_id(association.file_id)
        if not file_db:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found",
            )

        if file_db.uploader_id != current_user.id and current_user.role != Role.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to modify this association",
            )

        if update_data.order is not None:
            association = self.repository.update_order(association_id, update_data.order)
        if update_data.metadata is not None:
            association = self.repository.update_metadata(association_id, update_data.metadata)
        if update_data.category is not None:
            association = self.repository.update_category(association_id, update_data.category)

        return FileAssociationRead.model_validate(association)

    def reorder_associations(
        self,
        entity_type: str,
        entity_id: uuid.UUID,
        reorder_data: FileAssociationReorder,
        current_user: TokenData,
    ) -> List[FileAssociationRead]:
        """Reorder file associations for an entity."""
        if reorder_data.association_ids:
            first_assoc = self.repository.get_by_id(reorder_data.association_ids[0])
            if first_assoc:
                file_db = self.file_repository.get_by_id(first_assoc.file_id)
                if file_db and file_db.uploader_id != current_user.id and current_user.role != Role.ADMIN:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="You don't have permission to reorder these associations",
                    )

        associations = self.repository.reorder_associations(
            entity_type,
            entity_id,
            reorder_data.association_ids,
        )
        return [FileAssociationRead.model_validate(assoc) for assoc in associations]

    def delete_association(
        self,
        association_id: uuid.UUID,
        current_user: TokenData,
    ) -> None:
        """Delete a file association."""
        association = self.repository.get_by_id(association_id)
        if not association:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Association not found",
            )

        file_db = self.file_repository.get_by_id(association.file_id)
        if not file_db:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found",
            )

        if file_db.uploader_id != current_user.id and current_user.role != Role.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this association",
            )

        self.repository.delete(association)

    def delete_associations_by_entity(
        self,
        entity_type: str,
        entity_id: uuid.UUID,
        current_user: TokenData,
    ) -> None:
        """Delete all file associations for a specific entity."""
        associations = self.repository.get_by_entity(entity_type, entity_id)
        if associations:
            file_db = self.file_repository.get_by_id(associations[0].file_id)
            if file_db and file_db.uploader_id != current_user.id and current_user.role != Role.ADMIN:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to delete these associations",
                )

        self.repository.delete_by_entity(entity_type, entity_id)
