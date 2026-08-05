"""Application configuration.

A single Settings object, loaded once from environment variables (and a local
.env file in development). Nothing else in the codebase should read os.environ
directly — this is the one seam, so tests can override config without monkey-
patching the environment.
"""

from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# An obviously-fake placeholder, not a leaked credential — ruff's bandit rule
# (S105) flags any string literal assigned to a field named *key/*secret/
# *password on sight, which is the right default behavior for a scanner. The
# model_validator below is what actually makes this safe: the app refuses to
# start with this value outside local/test environments.
_PLACEHOLDER_SECRET_KEY = "change-me-in-every-real-environment"  # noqa: S105


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
    secret_key: str = _PLACEHOLDER_SECRET_KEY
    # Consumed by app/infra/security/jwt_token_service.py's JwtTokenService
    # — the one place these three values are read. Short access-token TTL
    # by design: an access token cannot be individually revoked (see
    # app.domain.auth.credential.Credential.token_version's own docstring
    # for what *can* be revoked, and why), so its blast radius if stolen
    # is bounded by how quickly it expires, not by any server-side check.
    access_token_ttl_minutes: int = 15
    refresh_token_ttl_days: int = 30
    jwt_algorithm: str = "HS256"
    # Consumed by app/composition/logging_config.py's configure_logging() —
    # the one place this value is read (see that module's own docstring for
    # why logging configuration is a Composition Root concern, not a
    # per-module `logging.getLogger(__name__).setLevel(...)` scattered
    # through the codebase). A plain str, not Python's own `int` level
    # constants, because it comes from an environment variable
    # (GYM_LOG_LEVEL) and gains nothing from a bespoke enum over the
    # standard level names logging.getLevelName() already understands.
    log_level: str = "INFO"

    @property
    def is_local(self) -> bool:
        return self.environment in ("local", "test")

    @model_validator(mode="after")
    def _reject_placeholder_secret_outside_local(self) -> "Settings":
        if self.secret_key == _PLACEHOLDER_SECRET_KEY and not self.is_local:
            msg = (
                "GYM_SECRET_KEY is still the placeholder value outside a local/test "
                "environment. Set a real secret via the environment before starting."
            )
            raise ValueError(msg)
        return self


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor — Settings() parses the environment once per process."""
    return Settings()
