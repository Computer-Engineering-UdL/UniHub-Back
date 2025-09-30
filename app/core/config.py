from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "UniRoom"
    API_V1_STR: str = "/api/v1"

    class Config:
        env_file = ".env"


settings = Settings()
