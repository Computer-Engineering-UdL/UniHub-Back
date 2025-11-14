import uuid
from typing import Generic, Type, TypeVar

from sqlalchemy.orm import Session

from app.core.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    A generic base repository with common CRUD operations for SQLAlchemy models.
    """

    def __init__(self, model: Type[ModelType], db: Session):
        """
        Initializes the repository with the database session and the specific model class.

        :param model: The SQLAlchemy model class.
        :param db: The SQLAlchemy Session object.
        """
        self.model_class = model
        self.db = db

    def get_by_id(self, entity_id: uuid.UUID) -> ModelType | None:
        """
        Retrieves an entity by its primary key (ID).

        :param entity_id: The UUID of the entity.
        :return: The entity instance or None if not found.
        """
        if entity_id is None:
            return None
        return self.db.get(self.model_class, entity_id)

    def delete(self, entity: ModelType) -> None:
        """
        Deletes a given entity instance from the database.

        :param entity: The entity instance to delete.
        """
        self.db.delete(entity)
        self.db.commit()
