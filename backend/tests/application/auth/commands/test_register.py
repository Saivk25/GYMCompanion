"""Tests for app/application/auth/commands/register.py."""

import pytest

from app.application.auth.commands.register import RegisterCommand
from app.domain.auth.value_objects import Email
from app.domain.user.value_objects import Locale, Timezone


@pytest.mark.unit
def test_carries_the_fields_it_was_given() -> None:
    command = RegisterCommand(
        email=Email("sai@example.com"),
        password="correct horse battery staple",
        locale=Locale("en"),
        timezone=Timezone("UTC"),
    )
    assert command.email == Email("sai@example.com")
    assert command.password == "correct horse battery staple"
    assert command.locale == Locale("en")
    assert command.timezone == Timezone("UTC")
