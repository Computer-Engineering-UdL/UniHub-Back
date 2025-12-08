import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.core.types import TokenData
from app.domains.connection.connection_service import ConnectionService
from app.literals.users import Role
from app.schemas import (
    ConnectionCreate,
    ConnectionList,
    ConnectionRead,
)

router = APIRouter()


def get_connection_service(db: Session = Depends(get_db)) -> ConnectionService:
    """Dependency to inject ConnectionService."""
    return ConnectionService(db)


# log connection
@router.post(
    "/",
    response_model=ConnectionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Log a new connection",
    response_description="Returns the created Connection entry.",
)
def log_connection(
    connection_in: ConnectionCreate,
    request: Request,
    service: ConnectionService = Depends(get_connection_service),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Log a connection entry.
    If the user is not Admin, forces user_id to match the token.
    """
    # Security: Ensure regular users can't log connections for others
    if current_user.role != Role.ADMIN:
        connection_in.user_id = current_user.id

    # Optional: If IP is not provided in body, try to get it from request (helper logic)
    # if not connection_in.ip_address:
    #     connection_in.ip_address = request.client.host

    return service.log_connection(connection_in)


# get my history
@router.get(
    "/me",
    response_model=List[ConnectionList],
    status_code=status.HTTP_200_OK,
    summary="Get current user connection history",
    response_description="Returns list of connections for the logged-in user.",
)
def get_my_connection_history(
    skip: int = 0,
    limit: int = 20,
    service: ConnectionService = Depends(get_connection_service),
    current_user: TokenData = Depends(get_current_user),
):
    """Get connection history for the current user."""
    return service.get_user_connection_history(
        user_id=current_user.id, skip=skip, limit=limit, current_user_id=current_user.id, is_admin=False
    )


# get history by user_id (admin)
@router.get(
    "/user/{user_id}",
    response_model=List[ConnectionList],
    status_code=status.HTTP_200_OK,
    summary="Get connection history by User ID",
    response_description="Returns list of connections for a specific user.",
)
def get_connection_history_by_user(
    user_id: uuid.UUID,
    skip: int = 0,
    limit: int = 50,
    service: ConnectionService = Depends(get_connection_service),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Get connection history for a specific user.
    Only Admins can view history of other users.
    """
    if current_user.role != Role.ADMIN and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Admin privileges required.")

    is_admin = current_user.role == Role.ADMIN

    return service.get_user_connection_history(
        user_id=user_id, skip=skip, limit=limit, current_user_id=current_user.id, is_admin=is_admin
    )


# search by ip (admin)
@router.get(
    "/ip/{ip_address}",
    response_model=List[ConnectionList],
    status_code=status.HTTP_200_OK,
    summary="Search connections by IP address",
    response_description="Returns list of connections from a specific IP.",
)
def get_connections_by_ip(
    ip_address: str,
    skip: int = 0,
    limit: int = 50,
    service: ConnectionService = Depends(get_connection_service),
    current_user: TokenData = Depends(get_current_user),
):
    """
    List all users who connected from a specific IP.
    Strictly Admin-only.
    """
    if current_user.role != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Admin privileges required.")

    return service.get_connections_by_ip(ip_address=ip_address, skip=skip, limit=limit, is_admin=True)
