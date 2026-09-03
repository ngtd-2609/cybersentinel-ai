from functools import lru_cache

from pydantic import model_validator
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

    auto_incident_risk_threshold: float = 85.0

    cors_origins: str = "http://localhost:3002"

    trusted_hosts: str = "api,localhost,127.0.0.1,testserver"

    login_rate_limit_attempts: int = 5

    login_rate_limit_window_seconds: int = 60

    enforce_production_config: bool = False

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def trusted_host_list(self) -> list[str]:
        return [item.strip() for item in self.trusted_hosts.split(",") if item.strip()]

    @model_validator(mode="after")
    def validate_production_secret(self) -> "Settings":
        if self.environment.lower() == "production" and self.enforce_production_config and (
            self.secret_key == "change-this-in-production"
            or len(self.secret_key) < 32
        ):
            raise ValueError(
                "CYBERSENTINEL_SECRET_KEY must be a unique value of at least "
                "32 characters in production"
            )
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="CYBERSENTINEL_",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
