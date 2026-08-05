"""Tests for app/application/auth/commands/logout.py."""

import pytest

from app.application.auth.commands.logout import LogoutCommand
from app.domain.user.identifiers import UserId


@pytest.mark.unit
def test_carries_the_user_id() -> None:
    user_id = UserId.generate()
    command = LogoutCommand(user_id=user_id)
    assert command.user_id == user_id
