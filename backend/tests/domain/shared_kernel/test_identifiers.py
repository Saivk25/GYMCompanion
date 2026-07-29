"""Tests for app/domain/shared_kernel/identifiers.py."""

import uuid

import pytest

from app.domain.shared_kernel.identifiers import EntityId


class _UserId(EntityId):
    """A throwaway subclass — real aggregate ID types (UserId, WorkoutId,
    ...) are added starting Sprint 2, alongside the aggregates that need
    them. This file only tests the base type's own behavior."""


class _WorkoutId(EntityId):
    pass


@pytest.mark.unit
def test_generate_returns_the_subclass_type() -> None:
    generated = _UserId.generate()
    assert isinstance(generated, _UserId)
    assert isinstance(generated.value, uuid.UUID)


@pytest.mark.unit
def test_generate_is_random() -> None:
    assert _UserId.generate() != _UserId.generate()


@pytest.mark.unit
def test_parse_round_trips_through_str() -> None:
    original = _UserId.generate()
    parsed = _UserId.parse(str(original))
    assert parsed == original
    assert isinstance(parsed, _UserId)


@pytest.mark.unit
def test_parse_rejects_malformed_input_with_a_clear_error() -> None:
    with pytest.raises(ValueError, match="not a valid identifier"):
        _UserId.parse("not-a-uuid")


@pytest.mark.unit
def test_different_subclasses_with_the_same_uuid_are_not_equal() -> None:
    """The entire point of subclassing per aggregate: a UserId and a
    WorkoutId that happen to wrap the same UUID value must never compare
    equal — mixing them up should be impossible, not just discouraged."""
    shared_value = uuid.uuid4()
    user_id = _UserId(shared_value)
    workout_id = _WorkoutId(shared_value)
    # mypy flags comparing two unrelated EntityId subclasses as a probable
    # typo (comparison-overlap) — here it's exactly the point of the test,
    # not a mistake.
    assert user_id != workout_id  # type: ignore[comparison-overlap]


@pytest.mark.unit
def test_str_returns_the_plain_uuid_string() -> None:
    raw = uuid.uuid4()
    assert str(_UserId(raw)) == str(raw)


@pytest.mark.unit
def test_is_frozen() -> None:
    entity_id = _UserId.generate()
    with pytest.raises(AttributeError):
        entity_id.value = uuid.uuid4()  # type: ignore[misc]
