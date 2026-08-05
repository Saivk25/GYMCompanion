"""Tests for app/application/readiness/commands/delete_readiness.py."""

from dataclasses import FrozenInstanceError

import pytest

from app.application.readiness.commands.delete_readiness import DeleteReadinessCommand
from app.application.shared.command import Command
from app.domain.readiness.identifiers import ReadinessId
from app.domain.user.identifiers import UserId


def _a_command() -> DeleteReadinessCommand:
    return DeleteReadinessCommand(
        readiness_id=ReadinessId.generate(), requester_id=UserId.generate()
    )


@pytest.mark.unit
def test_delete_readiness_command_is_a_command() -> None:
    assert isinstance(_a_command(), Command)


@pytest.mark.unit
def test_delete_readiness_command_exposes_its_readiness_id() -> None:
    readiness_id = ReadinessId.generate()
    command = DeleteReadinessCommand(readiness_id=readiness_id, requester_id=UserId.generate())
    assert command.readiness_id == readiness_id


@pytest.mark.unit
def test_delete_readiness_command_is_immutable() -> None:
    command = _a_command()
    with pytest.raises(FrozenInstanceError):
        command.readiness_id = ReadinessId.generate()  # type: ignore[misc]
