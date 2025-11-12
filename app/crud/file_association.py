import uuid
from typing import List, Optional

from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from app.models import FileAssociation
from app.schemas import FileAssociationCreate


class FileAssociationCRUD:
    """CRUD operations for file associations."""

    @staticmethod
    def create(db: Session, association_data: FileAssociationCreate) -> FileAssociation:
        """Create a new file association."""
        db_association = FileAssociation(**association_data.model_dump())
        db.add(db_association)
        db.commit()
        db.refresh(db_association)
        return db_association

    @staticmethod
    def bulk_create(db: Session, associations: List[FileAssociationCreate]) -> List[FileAssociation]:
        """Create multiple file associations at once."""
        db_associations = [FileAssociation(**assoc.model_dump()) for assoc in associations]
        db.add_all(db_associations)
        db.commit()
        for assoc in db_associations:
            db.refresh(assoc)
        return db_associations

    @staticmethod
    def get_by_id(db: Session, association_id: uuid.UUID) -> Optional[FileAssociation]:
        """Get a specific file association by ID."""
        return db.query(FileAssociation).filter(FileAssociation.id == association_id).one_or_none()

    @staticmethod
    def get_by_entity(
        db: Session, entity_type: str, entity_id: uuid.UUID, category: Optional[str] = None
    ) -> List[FileAssociation]:
        """
        Get all file associations for a specific entity.
        Optionally filter by category (e.g., 'photo', 'document').
        Results are ordered by the 'order' field.
        """
        query = db.query(FileAssociation).filter(
            FileAssociation.entity_type == entity_type, FileAssociation.entity_id == entity_id
        )

        if category:
            query = query.filter(FileAssociation.category == category)

        return query.order_by(FileAssociation.order).all()

    @staticmethod
    def get_by_file(db: Session, file_id: uuid.UUID) -> List[FileAssociation]:
        """Get all associations for a specific file."""
        return db.query(FileAssociation).filter(FileAssociation.file_id == file_id).all()

    @staticmethod
    def update_order(db: Session, association_id: uuid.UUID, new_order: int) -> FileAssociation:
        """Update the order of a file association."""
        association = db.query(FileAssociation).filter(FileAssociation.id == association_id).one_or_none()
        if not association:
            raise NoResultFound("File association not found")

        association.order = new_order
        db.commit()
        db.refresh(association)
        return association

    @staticmethod
    def update_metadata(db: Session, association_id: uuid.UUID, metadata: dict) -> FileAssociation:
        """Update metadata for a file association."""
        association = db.query(FileAssociation).filter(FileAssociation.id == association_id).one_or_none()
        if not association:
            raise NoResultFound("File association not found")

        association.metadata = metadata
        db.commit()
        db.refresh(association)
        return association

    @staticmethod
    def delete(db: Session, association_id: uuid.UUID) -> bool:
        """Delete a file association."""
        association = db.query(FileAssociation).filter(FileAssociation.id == association_id).one_or_none()
        if not association:
            raise NoResultFound("File association not found")

        db.delete(association)
        db.commit()
        return True

    @staticmethod
    def delete_by_entity(db: Session, entity_type: str, entity_id: uuid.UUID) -> int:
        """Delete all file associations for a specific entity. Returns count of deleted associations."""
        count = (
            db.query(FileAssociation)
            .filter(FileAssociation.entity_type == entity_type, FileAssociation.entity_id == entity_id)
            .delete()
        )
        db.commit()
        return count

    @staticmethod
    def delete_by_file(db: Session, file_id: uuid.UUID) -> int:
        """Delete all associations for a specific file. Returns count of deleted associations."""
        count = db.query(FileAssociation).filter(FileAssociation.file_id == file_id).delete()
        db.commit()
        return count

    @staticmethod
    def reorder_associations(
        db: Session, entity_type: str, entity_id: uuid.UUID, ordered_association_ids: List[uuid.UUID]
    ) -> List[FileAssociation]:
        """
        Reorder file associations for an entity.
        Pass a list of association IDs in the desired order.
        """
        associations = []
        for index, assoc_id in enumerate(ordered_association_ids):
            association = (
                db.query(FileAssociation)
                .filter(
                    FileAssociation.id == assoc_id,
                    FileAssociation.entity_type == entity_type,
                    FileAssociation.entity_id == entity_id,
                )
                .one_or_none()
            )

            if association:
                association.order = index
                associations.append(association)

        db.commit()
        for assoc in associations:
            db.refresh(assoc)

        return associations
