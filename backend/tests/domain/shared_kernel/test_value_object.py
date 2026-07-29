"""Tests for app/domain/shared_kernel/value_object.py."""

from dataclasses import FrozenInstanceError, dataclass

import pytest

from app.domain.shared_kernel.value_object import ValueObject


@dataclass(frozen=True)
class _Weight(ValueObject):
    kilograms: float
    label: str = "kg"


@pytest.mark.unit
def test_two_instances_with_equal_fields_are_equal() -> None:
    """Value semantics: no identity, only field values matter."""
    assert _Weight(20.0) == _Weight(20.0)


@pytest.mark.unit
def test_instances_with_different_fields_are_not_equal() -> None:
    assert _Weight(20.0) != _Weight(25.0)


@pytest.mark.unit
def test_is_immutable() -> None:
    weight = _Weight(20.0)
    with pytest.raises(FrozenInstanceError):
        weight.kilograms = 25.0  # type: ignore[misc]


@pytest.mark.unit
def test_is_hashable_and_usable_in_a_set() -> None:
    """Frozen + eq gives a generated __hash__ for free — worth proving,
    since a value object that can't go in a set/dict key is missing part
    of what "immutable value" is supposed to buy."""
    assert len({_Weight(20.0), _Weight(20.0), _Weight(25.0)}) == 2


@pytest.mark.unit
def test_subclass_without_frozen_true_fails_at_class_definition_time() -> None:
    """The enforcement mechanism this base class relies on (see its
    docstring): mixing a non-frozen dataclass into a frozen one's
    hierarchy is a TypeError from Python itself, not a convention someone
    has to remember to follow."""
    with pytest.raises(TypeError, match="frozen"):

        @dataclass  # not frozen=True
        class _BrokenValueObject(ValueObject):  # type: ignore[misc]
            oops: int
