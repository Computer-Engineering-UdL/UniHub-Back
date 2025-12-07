import uuid
from typing import List

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import ConnectionTableModel
from app.repositories.base import BaseRepository


class ConnectionRepository(BaseRepository[ConnectionTableModel]):
    """Repository for Connection entity."""

    def __init__(self, db: Session):
        super().__init__(ConnectionTableModel, db)
        self.model = self.model_class

    def create(self, connection_data: dict) -> ConnectionTableModel:
        """Create a new connection log."""
        connection = ConnectionTableModel(**connection_data)

        try:
            self.db.add(connection)
            self.db.commit()
            self.db.refresh(connection)
            return connection
        except IntegrityError as e:
            self.db.rollback()
            raise ValueError(f"Database integrity error: {str(e)}")
        except ValueError as e:
            # Catch validation error from Model's @ip_address.setter
            self.db.rollback()
            raise ValueError(str(e))
        except Exception:
            self.db.rollback()
            raise

    def get_by_user(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> List[ConnectionTableModel]:
        """Get all connections for a specific user, ordered by date desc."""
        stmt = (
            select(ConnectionTableModel)
            .filter(ConnectionTableModel.user_id == user_id)
            .order_by(ConnectionTableModel.connection_date.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def get_by_ip(
        self,
        ip_address: str,
        skip: int = 0,
        limit: int = 50,
    ) -> List[ConnectionTableModel]:
        """Get all connections from a specific IP address (exact match)."""
        # Note: Since model normalizes IP, ensure search term is normalized or use ilike if needed
        stmt = (
            select(ConnectionTableModel)
            # Use the underlying column name or property if queryable
            .filter(ConnectionTableModel._ip_address == ip_address)
            .order_by(ConnectionTableModel.connection_date.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())