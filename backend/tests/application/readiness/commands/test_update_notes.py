"""Tests for app/application/readiness/commands/update_notes.py."""

from dataclasses import FrozenInstanceError

import pytest

from app.application.readiness.commands.update_notes import UpdateNotesCommand
from app.application.shared.command import Command
from app.domain.readiness.identifiers import ReadinessId
from app.domain.readiness.value_objects import RecoveryNotes
from app.domain.user.identifiers import UserId


def _a_command() -> UpdateNotesCommand:
    return UpdateNotesCommand(
        readiness_id=ReadinessId.generate(),
        requester_id=UserId.generate(),
        notes=RecoveryNotes("felt sluggish"),
    )


@pytest.mark.unit
def test_update_notes_command_is_a_command() -> None:
    assert isinstance(_a_command(), Command)


@pytest.mark.unit
def test_update_notes_command_exposes_its_fields() -> None:
    command = _a_command()
    assert command.notes == RecoveryNotes("felt sluggish")


@pytest.mark.unit
def test_update_notes_command_is_immutable() -> None:
    command = _a_command()
    with pytest.raises(FrozenInstanceError):
        command.notes = RecoveryNotes("changed")  # type: ignore[misc]
