from pathlib import Path

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "UniHub"
    PROJECT_NAME: str = "UniHub API"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 1
    API_VERSION: str = "/api/v1"

    POSTGRES_USER: str = "unihub"
    POSTGRES_PASSWORD: str = "test"
    POSTGRES_DB: str = "unihub"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: str = "5432"
    DEBUG: bool = False
    SECRET_KEY: str = "secret"
    ALGORITHM: str = "HS256"
    ENVIRONMENT: str = "dev"
    PROD_URL: str = "https://computer-engineering-udl.github.io/UniHub-Front"
    TEMPORARY_DB: bool = False
    DEFAULT_PASSWORD: str = "supersecret"

    GOOGLE_CLIENT_ID: str = "dummy"
    GOOGLE_CLIENT_SECRET: str = "dummy"
    GITHUB_CLIENT_ID: str = "dummy"
    GITHUB_CLIENT_SECRET: str = "dummy"

    VALKEY_PORT_NUMBER: str = "6379"
    VALKEY_HOST: str = "localhost"
    VALKEY_PASSWORD: str = "supersecret"
    VALKEY_TTL: int = 3600
    USE_FAKE_VALKEY: bool = False

    NUKE_COOLDOWN_SECONDS: int = 30

    MAX_FILE_SIZE: int = 10 * 1024 * 1024
    ALLOWED_FILE_TYPES: list[str] = [
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp",
    ]

    TESTING: bool = False

    VERIFICATION_TOKEN_EXPIRE_HOURS: int = 24
    VERIFICATION_SEND_COOLDOWN_SECONDS: int = 60

    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = 1
    PASSWORD_RESET_RATE_LIMIT_REQUESTS: int = 3
    PASSWORD_RESET_RATE_LIMIT_WINDOW: int = 3600

    PASSWORD_HISTORY_COUNT: int = 5
    PASSWORD_MIN_LENGTH: int = 8

    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@uniroom.com"

    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "files"
    MINIO_SECURE: bool = False

    IMAGE_COMPRESSION_ENABLED: bool = True
    IMAGE_COMPRESSION_QUALITY: int = 80
    IMAGE_MAX_WIDTH: int = 1920
    IMAGE_MAX_HEIGHT: int = 1080
    IMAGE_CONVERT_TO_WEBP: bool = True

    model_config = SettingsConfigDict(
        env_file=f"{Path(__file__).parent.parent.parent}/.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql://{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_HOST}:"
            f"{self.POSTGRES_PORT}/"
            f"{self.POSTGRES_DB}"
        )

    @computed_field
    @property
    def VALKEY_URL(self) -> str:
        return f"redis://:{self.VALKEY_PASSWORD}@{self.VALKEY_HOST}:{self.VALKEY_PORT_NUMBER}"

    @computed_field
    @property
    def FRONTEND_URL(self) -> str:
        return "http://localhost:3200" if self.ENVIRONMENT == "dev" else settings.PROD_URL


settings = Settings()
