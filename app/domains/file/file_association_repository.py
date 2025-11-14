import uuid
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from app.models import FileAssociation
from app.repositories.base import BaseRepository


class FileAssociationRepository(BaseRepository[FileAssociation]):
    """Repository for FileAssociation entity with specialized queries."""

    def __init__(self, db: Session):
        super().__init__(FileAssociation, db)
        self.model = self.model_class

    def create(self, association_data: dict) -> FileAssociation:
        """Create a new file association."""
        association = FileAssociation(**association_data)
        self.db.add(association)
        self.db.commit()
        self.db.refresh(association)
        return association

    def bulk_create(self, associations_data: List[dict]) -> List[FileAssociation]:
        """Create multiple file associations at once."""
        associations = [FileAssociation(**data) for data in associations_data]
        self.db.add_all(associations)
        self.db.commit()
        for assoc in associations:
            self.db.refresh(assoc)
        return associations

    def get_by_entity(
        self,
        entity_type: str,
        entity_id: uuid.UUID,
        category: Optional[str] = None,
    ) -> List[FileAssociation]:
        """
        Get all file associations for a specific entity.
        Optionally filter by category (e.g., 'photo', 'document').
        Results are ordered by the 'order' field.
        """
        stmt = select(FileAssociation).filter(
            FileAssociation.entity_type == entity_type,
            FileAssociation.entity_id == entity_id,
        )

        if category:
            stmt = stmt.filter(FileAssociation.category == category)

        stmt = stmt.order_by(FileAssociation.order)
        return list(self.db.scalars(stmt).all())

    def get_by_file(self, file_id: uuid.UUID) -> List[FileAssociation]:
        """Get all associations for a specific file."""
        stmt = select(FileAssociation).filter(FileAssociation.file_id == file_id)
        return list(self.db.scalars(stmt).all())

    def update_order(self, association_id: uuid.UUID, new_order: int) -> FileAssociation:
        """Update the order of a file association."""
        association = self.get_by_id(association_id)
        if not association:
            raise NoResultFound("File association not found")

        association.order = new_order
        self.db.commit()
        self.db.refresh(association)
        return association

    def update_metadata(self, association_id: uuid.UUID, metadata: dict) -> FileAssociation:
        """Update metadata for a file association."""
        association = self.get_by_id(association_id)
        if not association:
            raise NoResultFound("File association not found")

        association.file_metadata = metadata
        self.db.commit()
        self.db.refresh(association)
        return association

    def update_category(self, association_id: uuid.UUID, category: str) -> FileAssociation:
        """Update category for a file association."""
        association = self.get_by_id(association_id)
        if not association:
            raise NoResultFound("File association not found")

        association.category = category
        self.db.commit()
        self.db.refresh(association)
        return association

    def delete_by_entity(self, entity_type: str, entity_id: uuid.UUID) -> int:
        """Delete all file associations for a specific entity. Returns count of deleted associations."""
        stmt = select(FileAssociation).filter(
            FileAssociation.entity_type == entity_type,
            FileAssociation.entity_id == entity_id,
        )
        associations = list(self.db.scalars(stmt).all())
        count = len(associations)
        for assoc in associations:
            self.db.delete(assoc)
        self.db.commit()
        return count

    def delete_by_file(self, file_id: uuid.UUID) -> int:
        """Delete all associations for a specific file. Returns count of deleted associations."""
        stmt = select(FileAssociation).filter(FileAssociation.file_id == file_id)
        associations = list(self.db.scalars(stmt).all())
        count = len(associations)
        for assoc in associations:
            self.db.delete(assoc)
        self.db.commit()
        return count

    def reorder_associations(
        self,
        entity_type: str,
        entity_id: uuid.UUID,
        ordered_association_ids: List[uuid.UUID],
    ) -> List[FileAssociation]:
        """
        Reorder file associations for an entity.
        Pass a list of association IDs in the desired order.
        """
        associations = []
        for index, assoc_id in enumerate(ordered_association_ids):
            stmt = select(FileAssociation).filter(
                FileAssociation.id == assoc_id,
                FileAssociation.entity_type == entity_type,
                FileAssociation.entity_id == entity_id,
            )
            association = self.db.scalar(stmt)

            if association:
                association.order = index
                associations.append(association)

        self.db.commit()
        for assoc in associations:
            self.db.refresh(assoc)

        return associations
