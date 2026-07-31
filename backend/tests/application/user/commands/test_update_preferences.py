"""Tests for app/application/user/commands/update_preferences.py."""

from dataclasses import FrozenInstanceError

import pytest

from app.application.shared.command import Command
from app.application.user.commands.update_preferences import UpdatePreferencesCommand
from app.domain.user.identifiers import UserId
from app.domain.user.value_objects import UserPreferences


def _a_command() -> UpdatePreferencesCommand:
    return UpdatePreferencesCommand(
        user_id=UserId.generate(), preferences=UserPreferences(biometric_app_lock_enabled=True)
    )


@pytest.mark.unit
def test_update_preferences_command_is_a_command() -> None:
    assert isinstance(_a_command(), Command)


@pytest.mark.unit
def test_update_preferences_command_exposes_its_fields() -> None:
    user_id = UserId.generate()
    preferences = UserPreferences(biometric_app_lock_enabled=True)
    command = UpdatePreferencesCommand(user_id=user_id, preferences=preferences)
    assert command.user_id == user_id
    assert command.preferences == preferences


@pytest.mark.unit
def test_update_preferences_command_is_immutable() -> None:
    command = _a_command()
    with pytest.raises(FrozenInstanceError):
        command.user_id = UserId.generate()  # type: ignore[misc]
