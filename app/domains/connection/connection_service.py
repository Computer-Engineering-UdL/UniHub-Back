import uuid
from typing import List

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.domains.connection.connection_repository import ConnectionRepository
from app.schemas import (
    ConnectionCreate,
    ConnectionList,
    ConnectionRead,
)


class ConnectionService:
    """Service layer for connection logging business logic."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = ConnectionRepository(db)

    def log_connection(self, connection_in: ConnectionCreate) -> ConnectionRead:
        """
        Log a new user connection (login).
        """
        try:
            connection_data = connection_in.model_dump()

            # Repository .create calls the model, which triggers @ip_address.setter validation
            connection = self.repository.create(connection_data)

            return ConnectionRead.model_validate(connection)
        except ValueError as e:
            # Catch invalid IP address format raised by model
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to log connection: {e}")

    def get_user_connection_history(
            self,
            user_id: uuid.UUID,
            skip: int = 0,
            limit: int = 20,
            current_user_id: uuid.UUID = None,
            is_admin: bool = False,
    ) -> List[ConnectionList]:
        """
        List connection history for a user.
        Includes security check: users can only see their own history unless admin.
        """
        if current_user_id and current_user_id != user_id and not is_admin:
            raise HTTPException(status_code=403, detail="Not authorized to view this connection history.")

        connections = self.repository.get_by_user(user_id, skip, limit)

        # Mapping to List schema (lighter version)
        return [ConnectionList.model_validate(conn) for conn in connections]

    def get_connections_by_ip(
            self,
            ip_address: str,
            skip: int = 0,
            limit: int = 50,
            is_admin: bool = False,
    ) -> List[ConnectionList]:
        """
        List connections from a specific IP.
        Usually an admin-only feature to detect suspicious activity.
        """
        if not is_admin:
            raise HTTPException(status_code=403, detail="Not authorized to search connections by IP.")

        connections = self.repository.get_by_ip(ip_address, skip, limit)
        return [ConnectionList.model_validate(conn) for conn in connections]