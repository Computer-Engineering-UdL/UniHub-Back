import datetime
import uuid
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator

from app.core.config import settings


class FileAssociationBase(BaseModel):
    """Base schema for file associations."""

    file_id: uuid.UUID
    entity_type: str = Field(
        ...,
        max_length=50,
        description="Type of entity (e.g., 'housing_offer', 'user_profile')",
    )
    entity_id: uuid.UUID
    order: int = Field(default=0, description="Order for sorting multiple files")
    category: Optional[str] = Field(None, max_length=50, description="Optional category (e.g., 'photo', 'document')")


class FileAssociationCreate(FileAssociationBase):
    """Schema for creating a file association."""

    pass


class FileAssociationRead(FileAssociationBase):
    """Schema for reading a file association."""

    id: uuid.UUID
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class FileAssociationReadWithFileURL(FileAssociationBase):
    """Schema for reading a file association."""

    id: uuid.UUID
    created_at: datetime.datetime
    file: "FileWithURL"
    model_config = ConfigDict(from_attributes=True)


class FileAssociationUpdate(BaseModel):
    """Schema for updating file association metadata."""

    order: Optional[int] = None
    category: Optional[str] = None


class FileAssociationReorder(BaseModel):
    """Schema for reordering associations."""

    association_ids: list[uuid.UUID] = Field(..., description="List of association IDs in desired order")


class FileDetail(BaseModel):
    """File details without binary data."""

    id: uuid.UUID
    filename: str
    content_type: str
    file_size: int
    uploaded_at: datetime.datetime
    is_public: bool
    uploader_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


class FileWithURL(BaseModel):
    """File details with URL."""

    id: uuid.UUID
    filename: str
    content_type: str

    @computed_field
    def url(self) -> str:
        return f"{settings.API_VERSION}/files/public/{self.id}"

    model_config = ConfigDict(from_attributes=True)


class FileAssociationWithFile(BaseModel):
    """Schema exposing only the file URL (no nested file object)."""

    id: uuid.UUID
    entity_type: str
    entity_id: uuid.UUID
    order: int
    category: str | None
    file_metadata: dict | None
    file_id: uuid.UUID
    is_public: bool = Field(default=False, exclude=True)

    @computed_field
    def url(self) -> str | None:
        if self.is_public:
            return f"{settings.API_VERSION}/files/public/{self.file_id}"
        return None

    @model_validator(mode="before")
    @classmethod
    def extract_file_data(cls, data: Any) -> Any:
        if hasattr(data, "file"):
            data_dict = {}
            for key in ["id", "entity_type", "entity_id", "order", "category", "file_metadata"]:
                if hasattr(data, key):
                    data_dict[key] = getattr(data, key)

            if hasattr(data, "file") and data.file is not None:
                data_dict["file_id"] = data.file.id
                data_dict["is_public"] = getattr(data.file, "is_public", False)

            return data_dict
        return data

    model_config = ConfigDict(from_attributes=True)


FileAssociationWithFile.model_rebuild()

__all__ = [
    "FileAssociationBase",
    "FileAssociationCreate",
    "FileAssociationRead",
    "FileAssociationUpdate",
    "FileAssociationReorder",
    "FileDetail",
    "FileAssociationWithFile",
]
