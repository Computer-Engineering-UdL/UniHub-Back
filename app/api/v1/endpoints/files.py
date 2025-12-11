from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, require_verified_email
from app.api.utils import handle_api_errors
from app.core.database import get_db
from app.core.types import TokenData
from app.domains.file.file_service import FileService
from app.schemas import FileDetail, FileList, FileUpload, VisibilityUpdate

router = APIRouter()


def get_file_service(db: Session = Depends(get_db)) -> FileService:
    """Dependency to inject FileService."""
    return FileService(db)


@router.post("/", response_model=FileUpload)
@handle_api_errors()
async def upload_file(
    file: UploadFile = File(...),
    is_public: bool = Form(False),
    service: FileService = Depends(get_file_service),
    current_user: TokenData = Depends(require_verified_email),
):
    """
    Endpoint to handle file uploads.
    Rate limited to 10 uploads per hour with 5 second cooldown between uploads.
    """
    return await service.upload_file(file, is_public, current_user)


@router.get("/public/{file_id}")
@handle_api_errors()
def view_public_file(
    file_id: str,
    service: FileService = Depends(get_file_service),
):
    """
    Public endpoint to view/serve publicly accessible files.
    No authentication required. Rate limited to 100 requests per minute.
    """
    return service.view_public_file(file_id)


@router.patch("/{file_id}/visibility")
@handle_api_errors()
def update_file_visibility(
    file_id: str,
    payload: VisibilityUpdate,
    service: FileService = Depends(get_file_service),
    current_user: TokenData = Depends(require_verified_email),
):
    """
    Update file visibility (public/private).
    Only file owner or admin can update.
    """
    return service.update_file_visibility(file_id, payload, current_user)


@router.get("/{file_id}", response_model=FileDetail)
@handle_api_errors()
def get_file_detail(
    file_id: str,
    service: FileService = Depends(get_file_service),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Endpoint to retrieve file details by ID.
    Requires authentication. Rate limited to 100 requests per minute.
    """
    return service.get_file_detail(file_id, current_user)


@router.get("/{file_id}/download")
@handle_api_errors()
def download_file(
    file_id: str,
    service: FileService = Depends(get_file_service),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Endpoint to download the actual file content.
    Requires authentication. Rate limited to 50 downloads per minute.
    """
    return service.download_file(file_id, current_user)


@router.get("/{file_id}/view")
@handle_api_errors()
def view_file(
    file_id: str,
    service: FileService = Depends(get_file_service),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Endpoint to view file inline (for images, PDFs, etc.).
    Requires authentication. Rate limited to 50 views per minute.
    """
    return service.view_file(file_id, current_user)


@router.delete("/{file_id}", status_code=204)
@handle_api_errors()
def delete_file(
    file_id: str,
    service: FileService = Depends(get_file_service),
    current_user: TokenData = Depends(require_verified_email),
):
    """
    Endpoint to delete a file by ID.
    Only file owner or admin can delete. Has 2 second cooldown.
    """
    service.delete_file(file_id, current_user)


@router.get("/", response_model=list[FileList])
@handle_api_errors()
def list_files(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    service: FileService = Depends(get_file_service),
    current_user: TokenData = Depends(get_current_user),
):
    """
    List files uploaded by the current user.
    Admins can see all files.
    """
    return service.list_files(skip, limit, current_user)
