"""Shared test doubles and helpers for the User Application Use Cases'
test suite. Not itself a test file (no `test_` prefix).

`FakeUserRepository` and `FakeUnitOfWork` are minimal, fully in-memory
implementations of the abstract `UserRepository`/`UnitOfWork`
interfaces this package depends on — proving those interfaces are
actually usable, the same reasoning
`tests/application/shared/test_unit_of_work.py`'s own fake documents.
Both accept a `fail_on_*` flag so a test can simulate a repository- or
UnitOfWork-level failure (a duplicate id collision, a lost database
connection, ...) without needing a real database.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone
from typing import Any

from app.application.shared.domain_event_dispatcher import DomainEventDispatcher
from app.application.shared.unit_of_work import UnitOfWork
from app.domain.shared_kernel.clock import FixedClock
from app.domain.shared_kernel.events import DomainEvent
from app.domain.user.identifiers import UserId
from app.domain.user.repository import UserRepository
from app.domain.user.user import User

_A_FIXED_INSTANT = datetime(2026, 1, 1, tzinfo=timezone.utc)


def a_fixed_clock() -> FixedClock:
    """A `FixedClock` pinned to an arbitrary, fixed instant — see
    `tests/domain/user/factories.py`'s identical helper."""
    return FixedClock(_A_FIXED_INSTANT)


class FakeUserRepository(UserRepository):
    """An in-memory `UserRepository`. `fail_on_get`/`fail_on_add` make
    it raise on the next call to simulate an infrastructure-level
    failure — a duplicate id collision for `add`, a lost connection
    for `get`."""

    def __init__(
        self,
        users: dict[UserId, User] | None = None,
        *,
        fail_on_get: bool = False,
        fail_on_add: bool = False,
    ) -> None:
        self._users: dict[UserId, User] = dict(users) if users else {}
        self.fail_on_get = fail_on_get
        self.fail_on_add = fail_on_add
        self.added: list[User] = []
        self.removed: list[User] = []

    def get(self, entity_id: UserId) -> User | None:
        if self.fail_on_get:
            raise RuntimeError("repository unavailable")
        return self._users.get(entity_id)

    def add(self, aggregate: User) -> None:
        if self.fail_on_add:
            raise ValueError(f"user {aggregate.id} already exists")
        self.added.append(aggregate)
        self._users[aggregate.id] = aggregate

    def remove(self, aggregate: User) -> None:
        self.removed.append(aggregate)
        self._users.pop(aggregate.id, None)


class FakeUnitOfWork(UnitOfWork):
    """An in-memory `UnitOfWork` scoped to exactly one
    `FakeUserRepository`. `fail_on_commit` simulates `commit()` itself
    failing (e.g. a constraint violation only caught at flush time).
    """

    def __init__(self, repository: FakeUserRepository, *, fail_on_commit: bool = False) -> None:
        self.repository = repository
        self.fail_on_commit = fail_on_commit
        self.committed = False
        self.rolled_back = False
        self.commit_calls = 0
        self.rollback_calls = 0

    def commit(self) -> None:
        if self.fail_on_commit:
            raise RuntimeError("commit failed")
        self.committed = True
        self.commit_calls += 1

    def rollback(self) -> None:
        self.rolled_back = True
        self.rollback_calls += 1

    def get_repository(self, repository_type: type[Any]) -> Any:
        if repository_type is UserRepository:
            return self.repository
        raise KeyError(repository_type)  # pragma: no cover — never exercised, no other repo exists


class RecordingDispatcher(DomainEventDispatcher):
    """A `DomainEventDispatcher` that records every event it was asked
    to dispatch, in order, with no side effect beyond recording."""

    def __init__(self) -> None:
        self.dispatched: list[DomainEvent] = []

    def dispatch(self, events: Sequence[DomainEvent]) -> None:
        self.dispatched.extend(events)


class OrderTrackingDispatcher(DomainEventDispatcher):
    """A `DomainEventDispatcher` that appends `"dispatch"` to a shared
    `call_order` list — paired with `OrderTrackingUnitOfWork` (which
    appends `"commit"`/`"rollback"` to the same list) so a test can
    assert dispatch happened strictly after commit, not interleaved
    with or before it.
    """

    def __init__(self, call_order: list[str]) -> None:
        self._call_order = call_order
        self.dispatched: list[DomainEvent] = []

    def dispatch(self, events: Sequence[DomainEvent]) -> None:
        self._call_order.append("dispatch")
        self.dispatched.extend(events)


class OrderTrackingUnitOfWork(FakeUnitOfWork):
    """A `FakeUnitOfWork` that appends to a shared `call_order` list on
    every `commit()`/`rollback()` — see `OrderTrackingDispatcher`."""

    def __init__(
        self,
        repository: FakeUserRepository,
        call_order: list[str],
        *,
        fail_on_commit: bool = False,
    ) -> None:
        super().__init__(repository, fail_on_commit=fail_on_commit)
        self._call_order = call_order

    def commit(self) -> None:
        super().commit()
        self._call_order.append("commit")

    def rollback(self) -> None:
        super().rollback()
        self._call_order.append("rollback")
