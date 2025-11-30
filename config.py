"""Bot configuration."""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    telegram_bot_token: str
    supabase_url: str
    supabase_key: str
    supabase_direct_url: Optional[str] = None  # For migrations, optional
    environment: str = "development"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


settings = Settings()

