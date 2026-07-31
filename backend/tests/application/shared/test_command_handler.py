"""Tests for app/application/shared/command_handler.py."""

from dataclasses import dataclass

import pytest

from app.application.shared.application_result import ApplicationResult
from app.application.shared.command import Command
from app.application.shared.command_handler import CommandHandler
from app.application.shared.interfaces import Handler


@dataclass(frozen=True, kw_only=True)
class _CreateThingCommand(Command):
    name: str


@pytest.mark.unit
def test_command_handler_cannot_be_instantiated_directly() -> None:
    with pytest.raises(TypeError):
        CommandHandler()  # type: ignore[abstract]


@pytest.mark.unit
def test_command_handler_is_a_handler() -> None:
    class _CreateThingHandler(CommandHandler[_CreateThingCommand, str]):
        def handle(self, command: _CreateThingCommand) -> ApplicationResult[str]:
            return ApplicationResult.ok(command.name)

    handler = _CreateThingHandler()
    assert isinstance(handler, Handler)


@pytest.mark.unit
def test_a_complete_subclass_can_be_instantiated_and_used() -> None:
    class _CreateThingHandler(CommandHandler[_CreateThingCommand, str]):
        def handle(self, command: _CreateThingCommand) -> ApplicationResult[str]:
            return ApplicationResult.ok(f"created {command.name}")

    handler = _CreateThingHandler()
    result = handler.handle(_CreateThingCommand(name="widget"))
    assert result.success is True
    assert result.value == "created widget"
