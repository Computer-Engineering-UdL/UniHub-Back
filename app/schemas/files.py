from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.user import UserSimplified

if TYPE_CHECKING:
    pass


class FileBase(BaseModel):
    """Base schema for file-related operations"""

    filename: str = Field(..., description="Name of the file")
    content_type: str = Field(..., description="MIME type of the file")
    file_size: int = Field(..., description="Size of the file in bytes")

    model_config = ConfigDict(from_attributes=True)


class FileUploadRequest(FileBase):
    """Request schema for uploading a file"""

    file_data: bytes = Field(..., description="Binary data of the file")
    uploader_id: uuid.UUID = Field(..., description="ID of the user uploading the file")
    is_public: bool = Field(default=False, description="Whether the file is publicly accessible")


class FileUpload(FileBase):
    """Response schema after uploading a file"""

    id: uuid.UUID
    uploaded_at: datetime
    uploader_id: uuid.UUID
    is_public: bool
    public_url: Optional[str] = Field(None, description="Public URL if file is public")


class FileSimplified(BaseModel):
    """Simplified file schema for nested representations"""

    id: uuid.UUID
    public_url: Optional[str] = Field(None, description="Public URL if file is public")

    model_config = ConfigDict(from_attributes=True)


class FileList(FileBase):
    """Response schema for listing files"""

    id: uuid.UUID
    uploaded_at: datetime
    is_public: bool


class FileDetail(FileUpload):
    """Detailed response schema for a single file"""

    uploaded_by: UserSimplified


class FileContent(FileBase):
    """Response schema that includes the actual file content"""

    id: uuid.UUID
    uploaded_at: datetime
    uploader_id: uuid.UUID
    file_data: bytes = Field(..., description="Binary content of the file")


class VisibilityUpdate(BaseModel):
    """Schema for updating file visibility"""

    is_public: bool


__all__ = [
    "FileUpload",
    "FileList",
    "FileDetail",
    "FileUploadRequest",
    "FileContent",
    "VisibilityUpdate",
    "FileSimplified",
]
