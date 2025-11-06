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
    TEMPORARY_DB: bool = False
    DEFAULT_PASSWORD: str = "supersecret"

    GOOGLE_CLIENT_ID: str = "dummy"
    GOOGLE_CLIENT_SECRET: str = "dummy"
    GITHUB_CLIENT_ID: str = "dummy"
    GITHUB_CLIENT_SECRET: str = "dummy"

    VALKEY_PORT_NUMBER: str = "6379"
    VALKEY_HOST: str = "localhost"
    VALKEY_PASSWORD: str = "supersecret"
    USE_FAKE_VALKEY: bool = False

    NUKE_COOLDOWN_SECONDS: int = 30

    model_config = SettingsConfigDict(
        env_file=f"{Path(__file__).parent.parent.parent}/.env",
        env_file_encoding="utf-8",
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


settings = Settings()
