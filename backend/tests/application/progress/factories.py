"""Shared test doubles and helpers for the Progress Application Use
Cases' test suite. Not itself a test file (no `test_` prefix).

`FakeProgressRepository`/`FakeUserRepository` are minimal, fully
in-memory implementations of the abstract repository interfaces this
package depends on — the same "prove the interface is actually usable"
reasoning `tests/application/nutrition/factories.py` documents for its
own fakes. `FakeUnitOfWork` dispatches `get_repository()` across both
repository types this phase's handlers touch.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date, datetime, timezone
from typing import Any

from app.application.shared.domain_event_dispatcher import DomainEventDispatcher
from app.application.shared.unit_of_work import UnitOfWork
from app.domain.progress.enums import MeasurementUnit, ProgressSource
from app.domain.progress.identifiers import ProgressId
from app.domain.progress.progress import Progress
from app.domain.progress.repository import ProgressRepository
from app.domain.progress.value_objects import ProgressDate
from app.domain.shared_kernel.clock import FixedClock
from app.domain.shared_kernel.events import DomainEvent
from app.domain.user.identifiers import UserId
from app.domain.user.repository import UserRepository
from app.domain.user.user import User
from app.domain.user.value_objects import AuthMethod, Locale, Timezone

_A_FIXED_INSTANT = datetime(2026, 1, 1, tzinfo=timezone.utc)


def a_fixed_clock() -> FixedClock:
    """A `FixedClock` pinned to an arbitrary, fixed instant — see
    `tests/domain/user/factories.py`'s identical helper."""
    return FixedClock(_A_FIXED_INSTANT)


def a_registered_user() -> User:
    """An Active User — the common "referenced by a Progress record"
    starting point most handler tests in this package build on."""
    user = User.register(
        user_id=UserId.generate(),
        locale=Locale("en"),
        timezone=Timezone("UTC"),
        auth_method=AuthMethod("webauthn_passkey"),
        clock=a_fixed_clock(),
    )
    user.activate()
    user.pull_domain_events()
    return user


def a_recorded_progress(
    *,
    user_id: UserId | None = None,
    progress_date: ProgressDate | None = None,
) -> Progress:
    """A freshly recorded Progress check-in with no optional fields set,
    events drained — mirroring `tests/domain/progress/factories.py`'s
    `a_recorded_progress()`, but with events pulled (that domain-layer
    factory deliberately leaves them, since domain tests assert on them;
    this application-layer factory drains them, matching
    `a_recorded_nutrition()`'s identical choice, since handler tests
    assert on events the handler itself pulls after its own mutation,
    not leftover ones from setup)."""
    progress = Progress.record(
        progress_id=ProgressId.generate(),
        user_id=user_id or UserId.generate(),
        progress_date=progress_date or ProgressDate(date(2026, 1, 1)),
        unit=MeasurementUnit.METRIC,
        source=ProgressSource.MANUAL,
        clock=a_fixed_clock(),
    )
    progress.pull_domain_events()
    return progress


class FakeProgressRepository(ProgressRepository):
    """An in-memory `ProgressRepository`. `fail_on_get`/`fail_on_add`/
    `fail_on_list` make it raise on the next call to simulate an
    infrastructure-level failure — the same reasoning
    `tests/application/nutrition/factories.py`'s
    `FakeNutritionRepository` documents for itself."""

    def __init__(
        self,
        records: dict[ProgressId, Progress] | None = None,
        *,
        fail_on_get: bool = False,
        fail_on_add: bool = False,
        fail_on_list: bool = False,
    ) -> None:
        self._records: dict[ProgressId, Progress] = dict(records) if records else {}
        self.fail_on_get = fail_on_get
        self.fail_on_add = fail_on_add
        self.fail_on_list = fail_on_list
        self.added: list[Progress] = []
        self.removed: list[Progress] = []

    def get(self, entity_id: ProgressId) -> Progress | None:
        if self.fail_on_get:
            raise RuntimeError("repository unavailable")
        return self._records.get(entity_id)

    def add(self, aggregate: Progress) -> None:
        if self.fail_on_add:
            raise ValueError(f"progress record {aggregate.id} already exists")
        self.added.append(aggregate)
        self._records[aggregate.id] = aggregate

    def remove(self, aggregate: Progress) -> None:
        self.removed.append(aggregate)
        self._records.pop(aggregate.id, None)

    def list_by_user(self, user_id: UserId) -> Sequence[Progress]:
        if self.fail_on_list:
            raise RuntimeError("repository unavailable")
        return [record for record in self._records.values() if record.user_id == user_id]


class FakeUserRepository(UserRepository):
    """An in-memory `UserRepository`, existence-check-only from this
    phase's handlers' point of view — see
    `tests/application/nutrition/factories.py`'s identical fake."""

    def __init__(
        self,
        users: dict[UserId, User] | None = None,
        *,
        fail_on_get: bool = False,
    ) -> None:
        self._users: dict[UserId, User] = dict(users) if users else {}
        self.fail_on_get = fail_on_get
        self.added: list[User] = []
        self.removed: list[User] = []

    def get(self, entity_id: UserId) -> User | None:
        if self.fail_on_get:
            raise RuntimeError("repository unavailable")
        return self._users.get(entity_id)

    def add(self, aggregate: User) -> None:
        self.added.append(aggregate)
        self._users[aggregate.id] = aggregate

    def remove(self, aggregate: User) -> None:
        self.removed.append(aggregate)
        self._users.pop(aggregate.id, None)


class FakeUnitOfWork(UnitOfWork):
    """An in-memory `UnitOfWork` scoped to up to two fake repositories
    at once — `ProgressRepository`, `UserRepository` — dispatching
    `get_repository()` by exact requested type. Any repository a given
    test doesn't need defaults to an empty fake of the right type.
    `fail_on_commit` simulates `commit()` itself failing.
    """

    def __init__(
        self,
        *,
        records: FakeProgressRepository | None = None,
        users: FakeUserRepository | None = None,
        fail_on_commit: bool = False,
    ) -> None:
        self.records = records or FakeProgressRepository()
        self.users = users or FakeUserRepository()
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
        if repository_type is ProgressRepository:
            return self.records
        if repository_type is UserRepository:
            return self.users
        raise KeyError(repository_type)  # pragma: no cover — never exercised, no other repo exists


class RecordingDispatcher(DomainEventDispatcher):
    """A `DomainEventDispatcher` that records every event it was asked
    to dispatch, in order — see
    `tests/application/nutrition/factories.py`'s identical fake."""

    def __init__(self) -> None:
        self.dispatched: list[DomainEvent] = []

    def dispatch(self, events: Sequence[DomainEvent]) -> None:
        self.dispatched.extend(events)


class OrderTrackingDispatcher(DomainEventDispatcher):
    """A `DomainEventDispatcher` that appends `"dispatch"` to a shared
    `call_order` list — paired with `OrderTrackingUnitOfWork`. See
    `tests/application/nutrition/factories.py`'s identical fake."""

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
        *,
        records: FakeProgressRepository | None = None,
        users: FakeUserRepository | None = None,
        call_order: list[str],
        fail_on_commit: bool = False,
    ) -> None:
        super().__init__(records=records, users=users, fail_on_commit=fail_on_commit)
        self._call_order = call_order

    def commit(self) -> None:
        super().commit()
        self._call_order.append("commit")

    def rollback(self) -> None:
        super().rollback()
        self._call_order.append("rollback")
