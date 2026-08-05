"""Tests for app/application/auth/commands/refresh.py."""

import pytest

from app.application.auth.commands.refresh import RefreshCommand


@pytest.mark.unit
def test_carries_the_refresh_token() -> None:
    command = RefreshCommand(refresh_token="a-refresh-token")
    assert command.refresh_token == "a-refresh-token"
