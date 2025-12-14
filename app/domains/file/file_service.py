import io
import uuid
from typing import List

import starlette.status
from fastapi import HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.types import TokenData
from app.domains.file.file_repository import FileRepository
from app.domains.file.image_processor import image_processor
from app.domains.file.storage_service import storage_service
from app.literals.users import Role
from app.schemas import FileDetail, FileList, FileUpload, VisibilityUpdate


class FileService:
    """Service layer for file-related business logic."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = FileRepository(db)

    async def upload_file(
        self,
        file: UploadFile,
        is_public: bool,
        current_user: TokenData,
    ) -> FileUpload:
        """Handle file uploads."""
        content = await file.read()

        if len(content) > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=starlette.status.HTTP_413_CONTENT_TOO_LARGE,
                detail="File size exceeds the maximum limit.",
            )

        allowed_types = settings.ALLOWED_FILE_TYPES
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=starlette.status.HTTP_400_BAD_REQUEST,
                detail=f"File type {file.content_type} not allowed",
            )

        file_id = uuid.uuid4()

        processed_content = content
        final_content_type = file.content_type
        final_filename = file.filename

        if image_processor.can_process(file.content_type):
            processed_content, final_content_type = image_processor.process_image(content, file.content_type)
            if final_content_type != file.content_type and file.filename:
                base_name = file.filename.rsplit(".", 1)[0]
                if final_content_type == "image/webp":
                    final_filename = f"{base_name}.webp"
                elif final_content_type == "image/jpeg":
                    final_filename = f"{base_name}.jpg"

        storage_path, storage_type, file_data = storage_service.upload(
            file_id,
            processed_content,
            final_content_type,
            prefer_minio=True,
        )

        file_data_dict = {
            "id": file_id,
            "filename": final_filename,
            "content_type": final_content_type,
            "file_data": file_data,
            "file_size": len(processed_content),
            "uploader_id": current_user.id,
            "is_public": is_public,
            "storage_path": storage_path,
            "storage_type": storage_type,
        }

        created_file = self.repository.create(file_data_dict)

        response = FileUpload.model_validate(created_file)
        if created_file.is_public:
            response.public_url = f"{settings.API_VERSION}/files/public/{created_file.id}"

        return response

    def view_public_file(self, file_id: str, thumbnail_width: int = None):
        """Public endpoint to view/serve publicly accessible files."""
        try:
            uuid_obj = uuid.UUID(file_id)
        except ValueError:
            raise HTTPException(
                status_code=starlette.status.HTTP_400_BAD_REQUEST,
                detail="Invalid file ID format",
            )

        file_db = self.repository.get_public_file(uuid_obj)
        if not file_db:
            raise HTTPException(
                status_code=starlette.status.HTTP_404_NOT_FOUND,
                detail="Public file not found",
            )

        content = storage_service.download(
            file_db.storage_path,
            file_db.storage_type,
            file_db.file_data,
        )

        media_type = file_db.content_type
        filename = file_db.filename

        if thumbnail_width and image_processor.can_process(file_db.content_type):
            max_height = int(thumbnail_width * 0.75)
            content, media_type = image_processor.create_thumbnail(
                content, file_db.content_type, max_width=thumbnail_width, max_height=max_height
            )
            base_name = file_db.filename.rsplit(".", 1)[0] if file_db.filename else "thumbnail"
            filename = f"{base_name}_thumb.webp"

        return StreamingResponse(
            io.BytesIO(content),
            media_type=media_type,
            headers={
                "Content-Disposition": f"inline; filename={filename}",
                "X-Content-Type-Options": "nosniff",
                "Cache-Control": "public, max-age=3600",
            },
        )

    def update_file_visibility(
        self,
        file_id: str,
        payload: VisibilityUpdate,
        current_user: TokenData,
    ) -> FileUpload:
        """Update file visibility (public/private)."""
        try:
            uuid_obj = uuid.UUID(file_id)
        except ValueError:
            raise HTTPException(
                status_code=starlette.status.HTTP_400_BAD_REQUEST,
                detail="Invalid file ID format",
            )

        file_db = self.repository.get_by_id(uuid_obj)
        if not file_db:
            raise HTTPException(
                status_code=starlette.status.HTTP_404_NOT_FOUND,
                detail="File not found",
            )

        if file_db.uploader_id != current_user.id and current_user.role != Role.ADMIN:
            raise HTTPException(
                status_code=starlette.status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to modify this file",
            )

        updated_file = self.repository.update_visibility(uuid_obj, payload.is_public)

        response = FileUpload.model_validate(updated_file)
        if updated_file.is_public:
            response.public_url = f"{settings.API_VERSION}/files/public/{updated_file.id}"

        return response

    def get_file_detail(self, file_id: str, current_user: TokenData) -> FileDetail:
        """Retrieve file details by ID."""
        try:
            uuid_obj = uuid.UUID(file_id)
        except ValueError:
            raise HTTPException(
                status_code=starlette.status.HTTP_400_BAD_REQUEST,
                detail="Invalid file ID format",
            )

        file_db = self.repository.get_by_id(uuid_obj)
        if not file_db:
            raise HTTPException(
                status_code=starlette.status.HTTP_404_NOT_FOUND,
                detail="File not found",
            )

        if file_db.uploader_id != current_user.id and current_user.role != Role.ADMIN:
            raise HTTPException(
                status_code=starlette.status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this file",
            )

        return FileDetail.model_validate(file_db)

    def download_file(self, file_id: str, current_user: TokenData):
        """Download the actual file content."""
        try:
            uuid_obj = uuid.UUID(file_id)
        except ValueError:
            raise HTTPException(
                status_code=starlette.status.HTTP_400_BAD_REQUEST,
                detail="Invalid file ID format",
            )

        file_db = self.repository.get_by_id(uuid_obj)
        if not file_db:
            raise HTTPException(
                status_code=starlette.status.HTTP_404_NOT_FOUND,
                detail="File not found",
            )

        if file_db.uploader_id != current_user.id and current_user.role != Role.ADMIN:
            raise HTTPException(
                status_code=starlette.status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to download this file",
            )

        content = storage_service.download(
            file_db.storage_path,
            file_db.storage_type,
            file_db.file_data,
        )

        return StreamingResponse(
            io.BytesIO(content),
            media_type=file_db.content_type,
            headers={
                "Content-Disposition": f"attachment; filename={file_db.filename}",
                "X-Content-Type-Options": "nosniff",
            },
        )

    def view_file(self, file_id: str, current_user: TokenData):
        """View file inline (for images, PDFs, etc.)."""
        try:
            uuid_obj = uuid.UUID(file_id)
        except ValueError:
            raise HTTPException(
                status_code=starlette.status.HTTP_400_BAD_REQUEST,
                detail="Invalid file ID format",
            )

        file_db = self.repository.get_by_id(uuid_obj)
        if not file_db:
            raise HTTPException(
                status_code=starlette.status.HTTP_404_NOT_FOUND,
                detail="File not found",
            )

        if file_db.uploader_id != current_user.id and current_user.role != Role.ADMIN:
            raise HTTPException(
                status_code=starlette.status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this file",
            )

        content = storage_service.download(
            file_db.storage_path,
            file_db.storage_type,
            file_db.file_data,
        )

        return StreamingResponse(
            io.BytesIO(content),
            media_type=file_db.content_type,
            headers={
                "Content-Disposition": f"inline; filename={file_db.filename}",
                "X-Content-Type-Options": "nosniff",
                "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'",
            },
        )

    def delete_file(self, file_id: str, current_user: TokenData) -> None:
        """Delete a file by ID."""
        try:
            uuid_obj = uuid.UUID(file_id)
        except ValueError:
            raise HTTPException(
                status_code=starlette.status.HTTP_400_BAD_REQUEST,
                detail="Invalid file ID format",
            )

        file_db = self.repository.get_by_id(uuid_obj)
        if not file_db:
            raise HTTPException(
                status_code=starlette.status.HTTP_404_NOT_FOUND,
                detail="File not found",
            )

        if file_db.uploader_id != current_user.id and current_user.role != Role.ADMIN:
            raise HTTPException(
                status_code=starlette.status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this file",
            )

        storage_service.delete(file_db.storage_path, file_db.storage_type)
        self.repository.soft_delete(uuid_obj)

    def list_files(self, skip: int, limit: int, current_user: TokenData) -> List[FileList]:
        """List files uploaded by the current user or all files for admins."""
        if current_user.role == Role.ADMIN:
            files = self.repository.list_all(skip, limit)
        else:
            files = self.repository.list_by_user(current_user.id, skip, limit)

        return [FileList.model_validate(file) for file in files]
