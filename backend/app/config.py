from functools import lru_cache

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    environment: str = "local"
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    backend_cors_origins: list[AnyHttpUrl] = Field(
        default_factory=lambda: ["http://localhost:3000"]
    )

    database_url: str = "postgresql+asyncpg://repost:repost@localhost:5432/repost_ai"
    redis_url: str = "redis://localhost:6379/0"
    use_redis_queue: bool = False

    supabase_url: str | None = None
    supabase_anon_key: str | None = None
    supabase_service_role_key: str | None = None
    supabase_jwt_secret: str | None = None

    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    youtube_data_api_key: str | None = None

    lemon_squeezy_api_key: str | None = None
    lemon_squeezy_webhook_secret: str | None = None
    resend_api_key: str | None = None
    sentry_dsn: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
