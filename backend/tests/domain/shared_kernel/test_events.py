"""Tests for app/domain/shared_kernel/events.py."""

import uuid
from dataclasses import FrozenInstanceError, dataclass
from datetime import datetime, timezone

import pytest

from app.domain.shared_kernel.events import DomainEvent


@dataclass(frozen=True, kw_only=True)
class _SomethingHappened(DomainEvent):
    payload: str


@pytest.mark.unit
def test_event_id_is_auto_generated_and_unique() -> None:
    now = datetime.now(timezone.utc)
    first = _SomethingHappened(occurred_at=now, payload="a")
    second = _SomethingHappened(occurred_at=now, payload="a")
    assert isinstance(first.event_id, uuid.UUID)
    assert first.event_id != second.event_id


@pytest.mark.unit
def test_occurred_at_is_exactly_what_the_caller_supplied() -> None:
    """No hidden datetime.now() call inside the event — occurred_at is
    whatever the caller (via a Clock) said it was, verbatim."""
    fixed = datetime(2026, 3, 5, 12, 0, tzinfo=timezone.utc)
    event = _SomethingHappened(occurred_at=fixed, payload="a")
    assert event.occurred_at == fixed


@pytest.mark.unit
def test_rejects_a_naive_occurred_at() -> None:
    naive = datetime(2026, 3, 5, 12, 0)  # deliberately naive
    with pytest.raises(ValueError, match="timezone-aware"):
        _SomethingHappened(occurred_at=naive, payload="a")


@pytest.mark.unit
def test_is_immutable() -> None:
    event = _SomethingHappened(occurred_at=datetime.now(timezone.utc), payload="a")
    with pytest.raises(FrozenInstanceError):
        event.payload = "b"  # type: ignore[misc]


@pytest.mark.unit
def test_subclass_without_frozen_true_fails_at_class_definition_time() -> None:
    """Same enforcement mechanism as ValueObject, and for the same reason:
    an event that could be mutated after construction would break the
    "immutable record of something that already happened" contract."""
    with pytest.raises(TypeError, match="frozen"):

        @dataclass(kw_only=True)  # not frozen=True
        class _BrokenEvent(DomainEvent):  # type: ignore[misc]
            oops: int
