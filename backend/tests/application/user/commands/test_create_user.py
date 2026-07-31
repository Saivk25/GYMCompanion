"""Tests for app/application/user/commands/create_user.py."""

from dataclasses import FrozenInstanceError

import pytest

from app.application.shared.command import Command
from app.application.user.commands.create_user import CreateUserCommand
from app.domain.user.value_objects import AuthMethod, Locale, Timezone


def _a_command() -> CreateUserCommand:
    return CreateUserCommand(
        locale=Locale("en"), timezone=Timezone("UTC"), auth_method=AuthMethod("webauthn_passkey")
    )


@pytest.mark.unit
def test_create_user_command_is_a_command() -> None:
    assert isinstance(_a_command(), Command)


@pytest.mark.unit
def test_create_user_command_exposes_its_fields() -> None:
    command = _a_command()
    assert command.locale == Locale("en")
    assert command.timezone == Timezone("UTC")
    assert command.auth_method == AuthMethod("webauthn_passkey")


@pytest.mark.unit
def test_create_user_command_is_immutable() -> None:
    command = _a_command()
    with pytest.raises(FrozenInstanceError):
        command.locale = Locale("fr")  # type: ignore[misc]
