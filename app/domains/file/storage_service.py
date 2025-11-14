import io
import uuid
from typing import Optional, Tuple

from app.core.config import settings


class StorageService:
    """
    Storage service that automatically handles MinIO when available,
    falls back to database storage otherwise.
    """

    def __init__(self):
        self.minio_available = False
        self.minio_client = None
        self.bucket = getattr(settings, "MINIO_BUCKET", "files")

        self._init_minio()

    def _init_minio(self):
        """Initialize MinIO client if configuration is available."""
        try:
            if not all(
                [
                    hasattr(settings, "MINIO_ENDPOINT"),
                    hasattr(settings, "MINIO_ACCESS_KEY"),
                    hasattr(settings, "MINIO_SECRET_KEY"),
                ]
            ):
                return

            from minio import Minio

            self.minio_client = Minio(
                settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=getattr(settings, "MINIO_SECURE", False),
            )

            if not self.minio_client.bucket_exists(self.bucket):
                self.minio_client.make_bucket(self.bucket)

            self.minio_available = True
        except Exception:
            self.minio_available = False

    def upload(
        self,
        file_id: uuid.UUID,
        content: bytes,
        content_type: str,
        prefer_minio: bool = True,
    ) -> Tuple[Optional[str], str, Optional[bytes]]:
        """
        Upload file to available storage.
        Returns: (storage_path, storage_type, file_data_for_db)
        - If MinIO available: (object_path, "minio", None)
        - If MinIO unavailable: (None, "database", file_content)
        """
        if self.minio_available:
            try:
                object_name = f"files/{file_id}"
                self.minio_client.put_object(
                    self.bucket,
                    object_name,
                    io.BytesIO(content),
                    length=len(content),
                    content_type=content_type,
                )
                return object_name, "minio", None
            except Exception:
                pass

        return None, "database", content

    def download(
        self,
        storage_path: Optional[str],
        storage_type: str,
        file_data: Optional[bytes],
    ) -> bytes:
        """
        Download file from storage.
        Automatically handles both MinIO and database storage.
        """
        if storage_type == "minio" and self.minio_available and storage_path:
            try:
                response = self.minio_client.get_object(self.bucket, storage_path)
                try:
                    return response.read()
                finally:
                    response.close()
                    response.release_conn()
            except Exception:
                pass

        if file_data is None:
            raise ValueError("File data not available")
        return file_data

    def delete(self, storage_path: Optional[str], storage_type: str) -> bool:
        """Delete file from storage."""
        if storage_type == "minio" and self.minio_available and storage_path:
            try:
                self.minio_client.remove_object(self.bucket, storage_path)
                return True
            except Exception:
                return False

        return True


storage_service = StorageService()
