"""Application configuration.

A single Settings object, loaded once from environment variables (and a local
.env file in development). Nothing else in the codebase should read os.environ
directly — this is the one seam, so tests can override config without monkey-
patching the environment.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration, sourced from environment variables prefixed GYM_."""

    model_config = SettingsConfigDict(
        env_prefix="GYM_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: str = "local"
    database_url: str = "postgresql+psycopg://gymcompanion:gymcompanion@localhost:5432/gymcompanion"
    secret_key: str = "change-me-in-every-real-environment"

    @property
    def is_local(self) -> bool:
        return self.environment == "local"


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor — Settings() parses the environment once per process."""
    return Settings()
