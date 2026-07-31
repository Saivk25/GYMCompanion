"""Shared test doubles and helpers for the Nutrition Application Use
Cases' test suite. Not itself a test file (no `test_` prefix).

`FakeNutritionRepository`/`FakeUserRepository` are minimal, fully
in-memory implementations of the abstract repository interfaces this
package depends on — the same "prove the interface is actually usable"
reasoning `tests/application/workout/factories.py` documents for its
own fakes. `FakeUnitOfWork` dispatches `get_repository()` across both
repository types this phase's handlers touch.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date, datetime, timezone
from typing import Any

from app.application.shared.domain_event_dispatcher import DomainEventDispatcher
from app.application.shared.unit_of_work import UnitOfWork
from app.domain.nutrition.identifiers import NutritionId
from app.domain.nutrition.nutrition import Nutrition
from app.domain.nutrition.repository import NutritionRepository
from app.domain.nutrition.value_objects import NutritionDate
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
    """An Active User — the common "referenced by a Nutrition entry"
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


def a_recorded_nutrition(*, user_id: UserId | None = None) -> Nutrition:
    """A freshly recorded Nutrition entry with no optional fields set,
    events drained — mirroring `tests/domain/nutrition/factories.py`'s
    identical helper."""
    nutrition = Nutrition.record(
        nutrition_id=NutritionId.generate(),
        user_id=user_id or UserId.generate(),
        nutrition_date=NutritionDate(date(2026, 1, 1)),
        clock=a_fixed_clock(),
    )
    nutrition.pull_domain_events()
    return nutrition


class FakeNutritionRepository(NutritionRepository):
    """An in-memory `NutritionRepository`. `fail_on_get`/`fail_on_add`/
    `fail_on_list` make it raise on the next call to simulate an
    infrastructure-level failure — the same reasoning
    `tests/application/workout/factories.py`'s
    `FakeWorkoutRepository` documents for itself."""

    def __init__(
        self,
        entries: dict[NutritionId, Nutrition] | None = None,
        *,
        fail_on_get: bool = False,
        fail_on_add: bool = False,
        fail_on_list: bool = False,
    ) -> None:
        self._entries: dict[NutritionId, Nutrition] = dict(entries) if entries else {}
        self.fail_on_get = fail_on_get
        self.fail_on_add = fail_on_add
        self.fail_on_list = fail_on_list
        self.added: list[Nutrition] = []
        self.removed: list[Nutrition] = []

    def get(self, entity_id: NutritionId) -> Nutrition | None:
        if self.fail_on_get:
            raise RuntimeError("repository unavailable")
        return self._entries.get(entity_id)

    def add(self, aggregate: Nutrition) -> None:
        if self.fail_on_add:
            raise ValueError(f"nutrition entry {aggregate.id} already exists")
        self.added.append(aggregate)
        self._entries[aggregate.id] = aggregate

    def remove(self, aggregate: Nutrition) -> None:
        self.removed.append(aggregate)
        self._entries.pop(aggregate.id, None)

    def list_by_user(self, user_id: UserId) -> Sequence[Nutrition]:
        if self.fail_on_list:
            raise RuntimeError("repository unavailable")
        return [entry for entry in self._entries.values() if entry.user_id == user_id]


class FakeUserRepository(UserRepository):
    """An in-memory `UserRepository`, existence-check-only from this
    phase's handlers' point of view — see
    `tests/application/workout/factories.py`'s identical fake."""

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
    at once — `NutritionRepository`, `UserRepository` — dispatching
    `get_repository()` by exact requested type. Any repository a given
    test doesn't need defaults to an empty fake of the right type.
    `fail_on_commit` simulates `commit()` itself failing.
    """

    def __init__(
        self,
        *,
        entries: FakeNutritionRepository | None = None,
        users: FakeUserRepository | None = None,
        fail_on_commit: bool = False,
    ) -> None:
        self.entries = entries or FakeNutritionRepository()
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
        if repository_type is NutritionRepository:
            return self.entries
        if repository_type is UserRepository:
            return self.users
        raise KeyError(repository_type)  # pragma: no cover — never exercised, no other repo exists


class RecordingDispatcher(DomainEventDispatcher):
    """A `DomainEventDispatcher` that records every event it was asked
    to dispatch, in order — see
    `tests/application/workout/factories.py`'s identical fake."""

    def __init__(self) -> None:
        self.dispatched: list[DomainEvent] = []

    def dispatch(self, events: Sequence[DomainEvent]) -> None:
        self.dispatched.extend(events)


class OrderTrackingDispatcher(DomainEventDispatcher):
    """A `DomainEventDispatcher` that appends `"dispatch"` to a shared
    `call_order` list — paired with `OrderTrackingUnitOfWork`. See
    `tests/application/workout/factories.py`'s identical fake."""

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
        entries: FakeNutritionRepository | None = None,
        users: FakeUserRepository | None = None,
        call_order: list[str],
        fail_on_commit: bool = False,
    ) -> None:
        super().__init__(entries=entries, users=users, fail_on_commit=fail_on_commit)
        self._call_order = call_order

    def commit(self) -> None:
        super().commit()
        self._call_order.append("commit")

    def rollback(self) -> None:
        super().rollback()
        self._call_order.append("rollback")
