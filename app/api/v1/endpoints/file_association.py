import uuid
from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.api.utils import handle_api_errors
from app.core.database import get_db
from app.core.types import TokenData
from app.domains.file.file_association_service import FileAssociationService
from app.schemas import (
    FileAssociationCreate,
    FileAssociationRead,
    FileAssociationReorder,
    FileAssociationUpdate,
    FileAssociationWithFile,
)

router = APIRouter()


def get_file_association_service(db: Session = Depends(get_db)) -> FileAssociationService:
    """Dependency to inject FileAssociationService."""
    return FileAssociationService(db)


@router.post("/", response_model=FileAssociationRead, status_code=status.HTTP_201_CREATED)
@handle_api_errors()
def create_association(
    association_in: FileAssociationCreate,
    service: FileAssociationService = Depends(get_file_association_service),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Create a new file association.
    Verifies that the user owns the file being associated.
    Rate limited to 20 per hour with 2 second cooldown.
    """
    return service.create_association(association_in, current_user)


@router.post("/bulk", response_model=List[FileAssociationRead], status_code=status.HTTP_201_CREATED)
@handle_api_errors()
def create_associations_bulk(
    associations: List[FileAssociationCreate],
    service: FileAssociationService = Depends(get_file_association_service),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Create multiple file associations at once.
    Useful for uploading multiple photos to a housing offer.
    Rate limited to 10 bulk operations per hour with 5 second cooldown.
    """
    return service.create_associations_bulk(associations, current_user)


@router.get("/{association_id}", response_model=FileAssociationRead)
@handle_api_errors()
def get_association(
    association_id: uuid.UUID,
    service: FileAssociationService = Depends(get_file_association_service),
):
    """
    Get a specific file association by ID.
    Rate limited to 100 requests per minute.
    """
    return service.get_association(association_id)


@router.get("/entity/{entity_type}/{entity_id}", response_model=List[FileAssociationWithFile])
@handle_api_errors()
def get_associations_by_entity(
    entity_type: str,
    entity_id: uuid.UUID,
    category: str = None,
    service: FileAssociationService = Depends(get_file_association_service),
):
    """
    Get all file associations for a specific entity.
    Optional category filter (e.g., 'photo', 'document').
    Returns associations with full file details, ordered by the 'order' field.
    Rate limited to 100 requests per minute.
    """
    return service.get_associations_by_entity(entity_type, entity_id, category)


@router.patch("/{association_id}", response_model=FileAssociationRead)
@handle_api_errors()
def update_association(
    association_id: uuid.UUID,
    update_data: FileAssociationUpdate,
    service: FileAssociationService = Depends(get_file_association_service),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Update file association metadata or order.
    Only the file owner or admin can update.
    """
    return service.update_association(association_id, update_data, current_user)


@router.post("/entity/{entity_type}/{entity_id}/reorder", response_model=List[FileAssociationRead])
@handle_api_errors()
def reorder_associations(
    entity_type: str,
    entity_id: uuid.UUID,
    reorder_data: FileAssociationReorder,
    service: FileAssociationService = Depends(get_file_association_service),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Reorder file associations for an entity.
    Pass a list of association IDs in the desired order.
    """
    return service.reorder_associations(entity_type, entity_id, reorder_data, current_user)


@router.delete("/{association_id}", status_code=status.HTTP_204_NO_CONTENT)
@handle_api_errors()
def delete_association(
    association_id: uuid.UUID,
    service: FileAssociationService = Depends(get_file_association_service),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Delete a file association.
    Only the file owner or admin can delete.
    Has 2 second cooldown.
    """
    service.delete_association(association_id, current_user)


@router.delete("/entity/{entity_type}/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
@handle_api_errors()
def delete_associations_by_entity(
    entity_type: str,
    entity_id: uuid.UUID,
    service: FileAssociationService = Depends(get_file_association_service),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Delete all file associations for a specific entity.
    Useful when deleting a housing offer or user profile.
    Has 5 second cooldown.
    """
    service.delete_associations_by_entity(entity_type, entity_id, current_user)
