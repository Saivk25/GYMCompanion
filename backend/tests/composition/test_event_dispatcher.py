"""Tests for `LoggingDomainEventDispatcher` — proves dispatching is
actually observable (a log record is emitted per event), not just that
`dispatch()` returns without raising.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone

import pytest

from app.composition.event_dispatcher import LoggingDomainEventDispatcher
from app.domain.shared_kernel.events import DomainEvent

_CLOCK_TIME = datetime(2026, 1, 1, tzinfo=timezone.utc)


@dataclass(frozen=True, kw_only=True)
class _WidgetRenamed(DomainEvent):
    widget_id: str
    new_name: str


@pytest.mark.unit
def test_dispatch_logs_one_record_per_event(caplog: pytest.LogCaptureFixture) -> None:
    dispatcher = LoggingDomainEventDispatcher()
    events = (
        _WidgetRenamed(occurred_at=_CLOCK_TIME, widget_id="a", new_name="first"),
        _WidgetRenamed(occurred_at=_CLOCK_TIME, widget_id="b", new_name="second"),
    )

    with caplog.at_level(logging.INFO, logger="app.composition.event_dispatcher"):
        dispatcher.dispatch(events)

    messages = [
        record.getMessage()
        for record in caplog.records
        if record.name == "app.composition.event_dispatcher"
    ]
    assert len(messages) == 2
    assert all("_WidgetRenamed" in message for message in messages)


@pytest.mark.unit
def test_dispatch_of_an_empty_sequence_logs_nothing_and_does_not_raise(
    caplog: pytest.LogCaptureFixture,
) -> None:
    dispatcher = LoggingDomainEventDispatcher()
    with caplog.at_level(logging.INFO, logger="app.composition.event_dispatcher"):
        dispatcher.dispatch(())
    assert caplog.records == []
