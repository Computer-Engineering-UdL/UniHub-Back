import io
import uuid

import starlette.status
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from app.api.utils import handle_api_errors
from app.core import get_db
from app.core.config import settings
from app.core.dependencies import get_current_user
from app.core.types import TokenData
from app.crud.files import FileCRUD
from app.literals.users import Role
from app.schemas import FileDetail, FileList, FileUpload, FileUploadRequest, VisibilityUpdate

router = APIRouter()


@router.post("/", response_model=FileUpload)
@handle_api_errors()
async def upload_file(
    file: UploadFile = File(...),
    is_public: bool = Form(False),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
    request: Request = None,
):
    """
    Endpoint to handle file uploads.
    Rate limited to 10 uploads per hour with 5 second cooldown between uploads.
    """
    content = await file.read()

    if len(content) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=starlette.status.HTTP_413_CONTENT_TOO_LARGE, detail="File size exceeds the maximum limit."
        )

    allowed_types = settings.ALLOWED_FILE_TYPES
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=starlette.status.HTTP_400_BAD_REQUEST, detail=f"File type {file.content_type} not allowed"
        )

    file_upload_req = FileUploadRequest(
        filename=file.filename,
        content_type=file.content_type,
        file_data=content,
        file_size=len(content),
        uploader_id=current_user.id,
        is_public=is_public,
    )

    created_file = FileCRUD.create_file(db, file_upload_req)

    response = FileUpload.model_validate(created_file)
    if created_file.is_public:
        response.public_url = f"{settings.API_VERSION}/files/public/{created_file.id}"

    return response


@router.get("/public/{file_id}")
@handle_api_errors()
def view_public_file(file_id: str, db: Session = Depends(get_db), request: Request = None):
    """
    Public endpoint to view/serve publicly accessible files.
    No authentication required. Rate limited to 100 requests per minute.
    """
    try:
        uuid_obj = uuid.UUID(file_id)
    except ValueError:
        raise HTTPException(status_code=starlette.status.HTTP_400_BAD_REQUEST, detail="Invalid file ID format")

    try:
        file_db = FileCRUD.get_public_file(db, uuid_obj)
    except NoResultFound:
        raise HTTPException(status_code=starlette.status.HTTP_404_NOT_FOUND, detail="Public file not found")

    return StreamingResponse(
        io.BytesIO(file_db.file_data),
        media_type=file_db.content_type,
        headers={
            "Content-Disposition": f"inline; filename={file_db.filename}",
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "public, max-age=3600",
        },
    )


@router.patch("/{file_id}/visibility")
@handle_api_errors()
def update_file_visibility(
    file_id: str,
    payload: VisibilityUpdate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
    request: Request = None,
):
    """
    Update file visibility (public/private).
    Only file owner or admin can update.
    """
    try:
        uuid_obj = uuid.UUID(file_id)
    except ValueError:
        raise HTTPException(status_code=starlette.status.HTTP_400_BAD_REQUEST, detail="Invalid file ID format")

    file_db = FileCRUD.get_file_by_id(db, uuid_obj)

    if not file_db:
        raise HTTPException(status_code=starlette.status.HTTP_404_NOT_FOUND, detail="File not found")

    if file_db.uploader_id != current_user.id and current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=starlette.status.HTTP_403_FORBIDDEN, detail="You don't have permission to modify this file"
        )

    updated_file = FileCRUD.update_file_visibility(db, uuid_obj, payload.is_public)

    response = FileUpload.model_validate(updated_file)
    if updated_file.is_public:
        response.public_url = f"{settings.API_VERSION}/files/public/{updated_file.id}"

    return response


@router.get("/{file_id}", response_model=FileDetail)
@handle_api_errors()
def get_file_detail(
    file_id: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
    request: Request = None,
):
    """
    Endpoint to retrieve file details by ID.
    Requires authentication. Rate limited to 100 requests per minute.
    """

    try:
        uuid_obj = uuid.UUID(file_id)
    except ValueError:
        raise HTTPException(status_code=starlette.status.HTTP_400_BAD_REQUEST, detail="Invalid file ID format")

    file_db = FileCRUD.get_file_by_id(db, uuid_obj)

    if not file_db:
        raise HTTPException(status_code=starlette.status.HTTP_404_NOT_FOUND, detail="File not found")

    if file_db.uploader_id != current_user.id and current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=starlette.status.HTTP_403_FORBIDDEN, detail="You don't have permission to access this file"
        )

    return file_db


@router.get("/{file_id}/download")
@handle_api_errors()
def download_file(
    file_id: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
    request: Request = None,
):
    """
    Endpoint to download the actual file content.
    Requires authentication. Rate limited to 50 downloads per minute.
    """

    try:
        uuid_obj = uuid.UUID(file_id)
    except ValueError:
        raise HTTPException(status_code=starlette.status.HTTP_400_BAD_REQUEST, detail="Invalid file ID format")

    file_db = FileCRUD.get_file_by_id(db, uuid_obj)

    if not file_db:
        raise HTTPException(status_code=starlette.status.HTTP_404_NOT_FOUND, detail="File not found")

    if file_db.uploader_id != current_user.id and current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=starlette.status.HTTP_403_FORBIDDEN, detail="You don't have permission to download this file"
        )

    return StreamingResponse(
        io.BytesIO(file_db.file_data),
        media_type=file_db.content_type,
        headers={
            "Content-Disposition": f"attachment; filename={file_db.filename}",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.get("/{file_id}/view")
@handle_api_errors()
def view_file(
    file_id: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
    request: Request = None,
):
    """
    Endpoint to view file inline (for images, PDFs, etc.).
    Requires authentication. Rate limited to 50 views per minute.
    """

    try:
        uuid_obj = uuid.UUID(file_id)
    except ValueError:
        raise HTTPException(status_code=starlette.status.HTTP_400_BAD_REQUEST, detail="Invalid file ID format")

    file_db = FileCRUD.get_file_by_id(db, uuid_obj)

    if not file_db:
        raise HTTPException(status_code=starlette.status.HTTP_404_NOT_FOUND, detail="File not found")

    if file_db.uploader_id != current_user.id and current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=starlette.status.HTTP_403_FORBIDDEN, detail="You don't have permission to view this file"
        )

    return StreamingResponse(
        io.BytesIO(file_db.file_data),
        media_type=file_db.content_type,
        headers={
            "Content-Disposition": f"inline; filename={file_db.filename}",
            "X-Content-Type-Options": "nosniff",
            "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'",
        },
    )


@router.delete("/{file_id}", status_code=starlette.status.HTTP_204_NO_CONTENT)
@handle_api_errors()
def delete_file(
    file_id: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
    request: Request = None,
):
    """
    Endpoint to delete a file by ID.
    Only file owner or admin can delete. Has 2 second cooldown.
    """

    try:
        uuid_obj = uuid.UUID(file_id)
    except ValueError:
        raise HTTPException(status_code=starlette.status.HTTP_400_BAD_REQUEST, detail="Invalid file ID format")

    file_db = FileCRUD.get_file_by_id(db, uuid_obj)

    if not file_db:
        raise HTTPException(status_code=starlette.status.HTTP_404_NOT_FOUND, detail="File not found")

    if file_db.uploader_id != current_user.id and current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=starlette.status.HTTP_403_FORBIDDEN, detail="You don't have permission to delete this file"
        )

    FileCRUD.delete_file(db, uuid_obj)


@router.get("/", response_model=list[FileList])
@handle_api_errors()
def list_files(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
    request: Request = None,
):
    """
    List files uploaded by the current user.
    Admins can see all files.
    """
    if current_user.role == Role.ADMIN:
        return FileCRUD.list_files(db, skip, limit)
    else:
        return FileCRUD.list_files_by_user(db, current_user.id, skip, limit)
