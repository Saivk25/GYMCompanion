"""Tests for app/domain/shared_kernel/aggregate_root.py."""

from dataclasses import dataclass
from datetime import datetime, timezone

import pytest

from app.domain.shared_kernel.aggregate_root import AggregateRoot
from app.domain.shared_kernel.events import DomainEvent
from app.domain.shared_kernel.identifiers import EntityId


class _UserId(EntityId):
    pass


@dataclass(frozen=True, kw_only=True)
class _NameChanged(DomainEvent):
    new_name: str


class _User(AggregateRoot[_UserId]):
    def __init__(self, user_id: _UserId, display_name: str) -> None:
        super().__init__(user_id)
        self.display_name = display_name

    def rename(self, new_name: str, *, occurred_at: datetime) -> None:
        self.display_name = new_name
        self.record_event(_NameChanged(occurred_at=occurred_at, new_name=new_name))


@pytest.mark.unit
def test_new_aggregate_has_no_pending_events() -> None:
    user = _User(_UserId.generate(), "Alice")
    assert user.pull_domain_events() == []


@pytest.mark.unit
def test_recorded_events_are_returned_by_pull_domain_events() -> None:
    user = _User(_UserId.generate(), "Alice")
    now = datetime.now(timezone.utc)

    user.rename("Alicia", occurred_at=now)

    events = user.pull_domain_events()
    assert len(events) == 1
    assert isinstance(events[0], _NameChanged)
    assert events[0].new_name == "Alicia"


@pytest.mark.unit
def test_pull_domain_events_drains_the_buffer() -> None:
    """The core safety property: once pulled, an event cannot be pulled
    (and therefore cannot be accidentally published) a second time."""
    user = _User(_UserId.generate(), "Alice")
    now = datetime.now(timezone.utc)
    user.rename("Alicia", occurred_at=now)

    first_pull = user.pull_domain_events()
    second_pull = user.pull_domain_events()

    assert len(first_pull) == 1
    assert second_pull == []


@pytest.mark.unit
def test_multiple_mutations_accumulate_events_in_order() -> None:
    user = _User(_UserId.generate(), "Alice")
    now = datetime.now(timezone.utc)

    user.rename("Alicia", occurred_at=now)
    user.rename("Ali", occurred_at=now)

    events = user.pull_domain_events()
    names = []
    for event in events:
        assert isinstance(event, _NameChanged)
        names.append(event.new_name)
    assert names == ["Alicia", "Ali"]


@pytest.mark.unit
def test_is_still_an_entity() -> None:
    """AggregateRoot must not lose Entity's identity-based equality."""
    shared_id = _UserId.generate()
    assert _User(shared_id, "Alice") == _User(shared_id, "Bob")
