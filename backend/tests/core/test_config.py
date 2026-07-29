"""Tests for app/core/config.py — specifically the placeholder-secret guard."""

import pytest

from app.core.config import Settings


@pytest.mark.unit
def test_placeholder_secret_is_fine_in_local() -> None:
    settings = Settings(environment="local", secret_key="change-me-in-every-real-environment")
    assert settings.secret_key == "change-me-in-every-real-environment"


@pytest.mark.unit
def test_placeholder_secret_is_rejected_outside_local() -> None:
    with pytest.raises(ValueError, match="placeholder value"):
        Settings(environment="production", secret_key="change-me-in-every-real-environment")


@pytest.mark.unit
def test_real_secret_is_accepted_outside_local() -> None:
    settings = Settings(environment="production", secret_key="a-real-generated-secret")
    assert settings.secret_key == "a-real-generated-secret"
