"""Tests for app/application/shared/command.py."""

from dataclasses import FrozenInstanceError, dataclass

import pytest

from app.application.shared.command import Command


@pytest.mark.unit
def test_command_can_be_instantiated_directly() -> None:
    """Unlike an ABC, a plain marker dataclass with no abstract methods
    is directly instantiable — it is only ever used as a base in
    practice, but nothing prevents constructing it bare."""
    command = Command()
    assert isinstance(command, Command)


@pytest.mark.unit
def test_command_is_immutable() -> None:
    command = Command()
    with pytest.raises(FrozenInstanceError):
        command.anything = 1  # type: ignore[attr-defined]


@pytest.mark.unit
def test_a_subclass_forgetting_frozen_true_fails_at_class_definition_time() -> None:
    """The whole point of `Command` being a frozen dataclass itself
    (not a plain marker class): the enforcement trick
    `app.domain.shared_kernel.value_object.ValueObject` also uses."""
    with pytest.raises(TypeError):

        @dataclass
        class _NotFrozen(Command):  # type: ignore[misc]
            value: int = 0


@pytest.mark.unit
def test_a_well_formed_subclass_carries_its_own_fields() -> None:
    @dataclass(frozen=True, kw_only=True)
    class _LogWorkoutCommand(Command):
        workout_id: str

    command = _LogWorkoutCommand(workout_id="abc-123")
    assert command.workout_id == "abc-123"
    assert isinstance(command, Command)
