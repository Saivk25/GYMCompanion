"""Tests for app/application/auth/commands/login.py."""

import pytest

from app.application.auth.commands.login import LoginCommand
from app.domain.auth.value_objects import Email


@pytest.mark.unit
def test_carries_the_fields_it_was_given() -> None:
    command = LoginCommand(email=Email("sai@example.com"), password="correct horse battery staple")
    assert command.email == Email("sai@example.com")
    assert command.password == "correct horse battery staple"
