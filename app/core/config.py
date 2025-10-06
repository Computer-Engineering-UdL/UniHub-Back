from pathlib import Path

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "UniRoom"
    PROJECT_NAME: str = "UniRoom API"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    API_VERSION: str = "/api/v1"

    POSTGRES_USER: str = "uniroom"
    POSTGRES_PASSWORD: str = "test"
    POSTGRES_DB: str = "uniroom"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: str = "5432"
    DEBUG: bool = False

    model_config = SettingsConfigDict(env_file=f"{Path(__file__).parent.parent.parent}/.env", env_file_encoding="utf-8")

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


settings = Settings()
