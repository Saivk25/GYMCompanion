"""Tests for app/application/shared/domain_event_dispatcher.py."""

from collections.abc import Sequence
from datetime import datetime, timezone

import pytest

from app.application.shared.domain_event_dispatcher import DomainEventDispatcher
from app.domain.shared_kernel.events import DomainEvent


class _ThingHappened(DomainEvent):
    pass


class _RecordingDispatcher(DomainEventDispatcher):
    def __init__(self) -> None:
        self.dispatched: list[DomainEvent] = []

    def dispatch(self, events: Sequence[DomainEvent]) -> None:
        self.dispatched.extend(events)


@pytest.mark.unit
def test_dispatcher_cannot_be_instantiated_directly() -> None:
    with pytest.raises(TypeError):
        DomainEventDispatcher()  # type: ignore[abstract]


@pytest.mark.unit
def test_a_subclass_missing_dispatch_still_cannot_be_instantiated() -> None:
    class _IncompleteDispatcher(DomainEventDispatcher):
        pass

    with pytest.raises(TypeError):
        _IncompleteDispatcher()  # type: ignore[abstract]


@pytest.mark.unit
def test_dispatching_an_empty_sequence_does_nothing() -> None:
    dispatcher = _RecordingDispatcher()
    dispatcher.dispatch([])
    assert dispatcher.dispatched == []


@pytest.mark.unit
def test_dispatching_events_forwards_them_in_order() -> None:
    dispatcher = _RecordingDispatcher()
    first = _ThingHappened(occurred_at=datetime(2026, 1, 1, tzinfo=timezone.utc))
    second = _ThingHappened(occurred_at=datetime(2026, 1, 2, tzinfo=timezone.utc))

    dispatcher.dispatch([first, second])

    assert dispatcher.dispatched == [first, second]
