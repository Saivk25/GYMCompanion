"""Tests for app/application/user/commands/update_profile.py."""

from dataclasses import FrozenInstanceError

import pytest

from app.application.shared.command import Command
from app.application.user.commands.update_profile import UpdateProfileCommand
from app.domain.user.enums import ExperienceLevel
from app.domain.user.identifiers import UserId
from app.domain.user.value_objects import UserProfile


def _a_command() -> UpdateProfileCommand:
    return UpdateProfileCommand(
        user_id=UserId.generate(),
        profile=UserProfile(
            height_cm=178.0, birth_year=1998, experience_level=ExperienceLevel.BEGINNER
        ),
    )


@pytest.mark.unit
def test_update_profile_command_is_a_command() -> None:
    assert isinstance(_a_command(), Command)


@pytest.mark.unit
def test_update_profile_command_exposes_its_fields() -> None:
    user_id = UserId.generate()
    profile = UserProfile(
        height_cm=178.0, birth_year=1998, experience_level=ExperienceLevel.BEGINNER
    )
    command = UpdateProfileCommand(user_id=user_id, profile=profile)
    assert command.user_id == user_id
    assert command.profile == profile


@pytest.mark.unit
def test_update_profile_command_is_immutable() -> None:
    command = _a_command()
    with pytest.raises(FrozenInstanceError):
        command.user_id = UserId.generate()  # type: ignore[misc]
