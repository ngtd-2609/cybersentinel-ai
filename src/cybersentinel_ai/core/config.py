from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = (
        "postgresql+psycopg://postgres:postgres@localhost:5432/cybersentinel"
    )

    ollama_url: str = "http://localhost:11434"

    ollama_model: str = "qwen3:4b"

    app_name: str = "CyberSentinel AI"

    environment: str = "development"

    secret_key: str = "change-this-in-production"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="CYBERSENTINEL_",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
