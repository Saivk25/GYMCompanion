"""Tests for app/application/progress/commands/update_notes.py."""

from dataclasses import FrozenInstanceError

import pytest

from app.application.progress.commands.update_notes import UpdateNotesCommand
from app.application.shared.command import Command
from app.domain.progress.identifiers import ProgressId
from app.domain.progress.value_objects import ProgressNotes


def _a_command() -> UpdateNotesCommand:
    return UpdateNotesCommand(
        progress_id=ProgressId.generate(), notes=ProgressNotes("measured fasted")
    )


@pytest.mark.unit
def test_update_notes_command_is_a_command() -> None:
    assert isinstance(_a_command(), Command)


@pytest.mark.unit
def test_update_notes_command_exposes_its_fields() -> None:
    command = _a_command()
    assert command.notes == ProgressNotes("measured fasted")


@pytest.mark.unit
def test_update_notes_command_is_immutable() -> None:
    command = _a_command()
    with pytest.raises(FrozenInstanceError):
        command.notes = ProgressNotes("changed")  # type: ignore[misc]
