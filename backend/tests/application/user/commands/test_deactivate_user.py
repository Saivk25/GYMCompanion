"""Tests for app/application/user/commands/deactivate_user.py."""

from dataclasses import FrozenInstanceError

import pytest

from app.application.shared.command import Command
from app.application.user.commands.deactivate_user import DeactivateUserCommand
from app.domain.user.identifiers import UserId


@pytest.mark.unit
def test_deactivate_user_command_is_a_command() -> None:
    assert isinstance(DeactivateUserCommand(user_id=UserId.generate()), Command)


@pytest.mark.unit
def test_deactivate_user_command_exposes_its_field() -> None:
    user_id = UserId.generate()
    command = DeactivateUserCommand(user_id=user_id)
    assert command.user_id == user_id


@pytest.mark.unit
def test_deactivate_user_command_is_immutable() -> None:
    command = DeactivateUserCommand(user_id=UserId.generate())
    with pytest.raises(FrozenInstanceError):
        command.user_id = UserId.generate()  # type: ignore[misc]
