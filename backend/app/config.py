from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"

    database_url: str = "postgresql://travel:CHANGE_ME@postgres:5432/japan_travel"

    ai_api_key: str = ""
    maps_api_key: str = ""

    secret_key: str = "CHANGE_ME"

    frontend_url: str = "http://localhost:3000"
    backend_url: str = "http://localhost:8000"


@lru_cache
def get_settings() -> Settings:
    return Settings()
