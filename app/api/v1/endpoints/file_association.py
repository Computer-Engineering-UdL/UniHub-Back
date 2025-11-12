import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from app.api.utils import handle_api_errors
from app.core.database import get_db
from app.core.dependencies import cooldown, get_current_user, rate_limit
from app.core.types import TokenData
from app.crud.file_association import FileAssociationCRUD
from app.crud.files import FileCRUD
from app.literals.users import Role
from app.schemas import (
    FileAssociationCreate,
    FileAssociationRead,
    FileAssociationReorder,
    FileAssociationUpdate,
    FileAssociationWithFile,
)

router = APIRouter()


@router.post("/", response_model=FileAssociationRead, status_code=status.HTTP_201_CREATED)
@rate_limit(max_requests=20, window_seconds=3600, key_prefix="file_association_create")
@cooldown(action="file_association_create", cooldown_seconds=2)
@handle_api_errors()
def create_association(
    association_in: FileAssociationCreate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
    request: Request = None,
):
    """
    Create a new file association.
    Verifies that the user owns the file being associated.
    Rate limited to 20 per hour with 2 second cooldown.
    """

    try:
        file_db = FileCRUD.get_file_by_id(db, association_in.file_id)
        if file_db.uploader_id != current_user.id and current_user.role != Role.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="You don't have permission to use this file"
            )
    except NoResultFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    return FileAssociationCRUD.create(db, association_in)


@router.post("/bulk", response_model=List[FileAssociationRead], status_code=status.HTTP_201_CREATED)
@rate_limit(max_requests=10, window_seconds=3600, key_prefix="file_association_bulk")
@cooldown(action="file_association_bulk", cooldown_seconds=5)
@handle_api_errors()
def create_associations_bulk(
    associations: List[FileAssociationCreate],
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
    request: Request = None,
):
    """
    Create multiple file associations at once.
    Useful for uploading multiple photos to a housing offer.
    Rate limited to 10 bulk operations per hour with 5 second cooldown.
    """

    for assoc in associations:
        try:
            file_db = FileCRUD.get_file_by_id(db, assoc.file_id)
            if file_db.uploader_id != current_user.id and current_user.role != Role.ADMIN:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"You don't have permission to use file {assoc.file_id}",
                )
        except NoResultFound:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"File {assoc.file_id} not found")

    return FileAssociationCRUD.bulk_create(db, associations)


@router.get("/{association_id}", response_model=FileAssociationRead)
@rate_limit(max_requests=100, window_seconds=60, key_prefix="file_association_detail")
@handle_api_errors()
def get_association(
    association_id: uuid.UUID,
    db: Session = Depends(get_db),
    request: Request = None,
):
    """
    Get a specific file association by ID.
    Rate limited to 100 requests per minute.
    """
    association = FileAssociationCRUD.get_by_id(db, association_id)
    if not association:
        raise HTTPException(status_code=404, detail="Association not found")
    return association


@router.get("/entity/{entity_type}/{entity_id}", response_model=List[FileAssociationWithFile])
@rate_limit(max_requests=100, window_seconds=60, key_prefix="file_association_by_entity")
@handle_api_errors()
def get_associations_by_entity(
    entity_type: str,
    entity_id: uuid.UUID,
    category: str = None,
    db: Session = Depends(get_db),
    request: Request = None,
):
    """
    Get all file associations for a specific entity.
    Optional category filter (e.g., 'photo', 'document').
    Returns associations with full file details, ordered by the 'order' field.
    Rate limited to 100 requests per minute.
    """
    return FileAssociationCRUD.get_by_entity(db, entity_type, entity_id, category)


@router.patch("/{association_id}", response_model=FileAssociationRead)
@handle_api_errors()
def update_association(
    association_id: uuid.UUID,
    update_data: FileAssociationUpdate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
    request: Request = None,
):
    """
    Update file association metadata or order.
    Only the file owner or admin can update.
    """
    association = FileAssociationCRUD.get_by_id(db, association_id)
    if not association:
        raise HTTPException(status_code=404, detail="Association not found")

    file_db = FileCRUD.get_file_by_id(db, association.file_id)
    if file_db.uploader_id != current_user.id and current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="You don't have permission to modify this association"
        )

    if update_data.order is not None:
        association = FileAssociationCRUD.update_order(db, association_id, update_data.order)
    if update_data.metadata is not None:
        association = FileAssociationCRUD.update_metadata(db, association_id, update_data.metadata)
    if update_data.category is not None:
        association.category = update_data.category
        db.commit()
        db.refresh(association)

    return association


@router.post("/entity/{entity_type}/{entity_id}/reorder", response_model=List[FileAssociationRead])
@handle_api_errors()
def reorder_associations(
    entity_type: str,
    entity_id: uuid.UUID,
    reorder_data: FileAssociationReorder,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
    request: Request = None,
):
    """
    Reorder file associations for an entity.
    Pass a list of association IDs in the desired order.
    """

    if reorder_data.association_ids:
        first_assoc = FileAssociationCRUD.get_by_id(db, reorder_data.association_ids[0])
        if first_assoc:
            file_db = FileCRUD.get_file_by_id(db, first_assoc.file_id)
            if file_db.uploader_id != current_user.id and current_user.role != Role.ADMIN:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to reorder these associations",
                )

    return FileAssociationCRUD.reorder_associations(db, entity_type, entity_id, reorder_data.association_ids)


@router.delete("/{association_id}", status_code=status.HTTP_204_NO_CONTENT)
@cooldown(action="file_association_delete", cooldown_seconds=2)
@handle_api_errors()
def delete_association(
    association_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
    request: Request = None,
):
    """
    Delete a file association.
    Only the file owner or admin can delete.
    Has 2 second cooldown.
    """
    association = FileAssociationCRUD.get_by_id(db, association_id)
    if not association:
        raise HTTPException(status_code=404, detail="Association not found")

    file_db = FileCRUD.get_file_by_id(db, association.file_id)
    if file_db.uploader_id != current_user.id and current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="You don't have permission to delete this association"
        )

    FileAssociationCRUD.delete(db, association_id)


@router.delete("/entity/{entity_type}/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
@cooldown(action="file_association_delete_entity", cooldown_seconds=5)
@handle_api_errors()
def delete_associations_by_entity(
    entity_type: str,
    entity_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
    request: Request = None,
):
    """
    Delete all file associations for a specific entity.
    Useful when deleting a housing offer or user profile.
    Has 5 second cooldown.
    """

    associations = FileAssociationCRUD.get_by_entity(db, entity_type, entity_id)
    if associations:
        file_db = FileCRUD.get_file_by_id(db, associations[0].file_id)
        if file_db.uploader_id != current_user.id and current_user.role != Role.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="You don't have permission to delete these associations"
            )

    FileAssociationCRUD.delete_by_entity(db, entity_type, entity_id)
