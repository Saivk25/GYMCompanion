"""Tests for app/application/progress/commands/delete_progress.py."""

from dataclasses import FrozenInstanceError

import pytest

from app.application.progress.commands.delete_progress import DeleteProgressCommand
from app.application.shared.command import Command
from app.domain.progress.identifiers import ProgressId
from app.domain.user.identifiers import UserId


def _a_command() -> DeleteProgressCommand:
    return DeleteProgressCommand(progress_id=ProgressId.generate(), requester_id=UserId.generate())


@pytest.mark.unit
def test_delete_progress_command_is_a_command() -> None:
    assert isinstance(_a_command(), Command)


@pytest.mark.unit
def test_delete_progress_command_exposes_its_progress_id() -> None:
    progress_id = ProgressId.generate()
    command = DeleteProgressCommand(progress_id=progress_id, requester_id=UserId.generate())
    assert command.progress_id == progress_id


@pytest.mark.unit
def test_delete_progress_command_is_immutable() -> None:
    command = _a_command()
    with pytest.raises(FrozenInstanceError):
        command.progress_id = ProgressId.generate()  # type: ignore[misc]
