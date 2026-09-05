from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/cybersentinel"

    ollama_url: str = "http://localhost:11434"

    ollama_model: str = "qwen3:4b"

    app_name: str = "CyberSentinel AI"

    environment: str = "development"

    secret_key: str = "change-this-in-production"

    auto_incident_risk_threshold: float = 85.0

    cors_origins: str = "http://localhost:3002"

    trusted_hosts: str = "api,localhost,127.0.0.1,testserver"

    login_rate_limit_attempts: int = Field(default=5, ge=1)

    login_rate_limit_window_seconds: int = Field(default=60, ge=1)

    redis_url: str | None = None

    rate_limit_fail_closed: bool = True

    trust_proxy_headers: bool = False

    ingestion_api_keys: str = ""

    ingestion_batch_size: int = Field(default=500, ge=1, le=5000)

    ingestion_max_attempts: int = Field(default=5, ge=1, le=20)

    ingestion_worker_poll_seconds: float = Field(default=1.0, ge=0.1, le=60.0)

    correlation_window_minutes: int = Field(default=30, ge=1, le=10080)

    notification_webhook_url: str | None = None

    notification_slack_webhook_url: str | None = None

    realtime_channel: str = "cybersentinel:soc-updates"

    public_registration_enabled: bool = False

    account_lockout_attempts: int = Field(default=5, ge=1)

    account_lockout_minutes: int = Field(default=15, ge=1)

    access_token_expire_minutes: int = 15

    refresh_token_expire_days: int = 7

    mfa_challenge_expire_minutes: int = Field(default=5, ge=1, le=15)

    mfa_challenge_max_attempts: int = Field(default=5, ge=1, le=10)

    enforce_production_config: bool = False

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def trusted_host_list(self) -> list[str]:
        return [item.strip() for item in self.trusted_hosts.split(",") if item.strip()]

    @property
    def ingestion_api_key_list(self) -> list[str]:
        return [item.strip() for item in self.ingestion_api_keys.split(",") if item.strip()]

    @model_validator(mode="after")
    def validate_production_secret(self) -> "Settings":
        if (
            self.environment.lower() == "production"
            and self.enforce_production_config
            and (self.secret_key == "change-this-in-production" or len(self.secret_key) < 32)
        ):
            raise ValueError(
                "CYBERSENTINEL_SECRET_KEY must be a unique value of at least "
                "32 characters in production"
            )
        if (
            self.environment.lower() == "production"
            and self.enforce_production_config
            and not self.redis_url
        ):
            raise ValueError("CYBERSENTINEL_REDIS_URL is required in production")
        if (
            self.environment.lower() == "production"
            and self.enforce_production_config
            and not self.ingestion_api_key_list
        ):
            raise ValueError("CYBERSENTINEL_INGESTION_API_KEYS is required in production")
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="CYBERSENTINEL_",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
