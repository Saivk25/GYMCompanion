"""Shared test doubles and helpers for the Workout Application Use
Cases' test suite. Not itself a test file (no `test_` prefix).

`FakeWorkoutRepository`, `FakeWorkoutSessionRepository`,
`FakeExerciseRepository`, and `FakeUserRepository` are minimal, fully
in-memory implementations of the abstract repository interfaces this
package depends on — the same "prove the interface is actually usable"
reasoning `tests/application/user/factories.py` documents for its own
single-repository fake, extended here to four repository types since
this phase's handlers orchestrate `Workout`, `WorkoutSession`,
`Exercise` (lookup only), and `User` (existence check only) together.
`FakeUnitOfWork` dispatches `get_repository()` by type across all four.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date, datetime, timezone
from typing import Any

from app.application.shared.domain_event_dispatcher import DomainEventDispatcher
from app.application.shared.unit_of_work import UnitOfWork
from app.domain.exercise.enums import Difficulty, MovementPattern
from app.domain.exercise.exercise import Exercise
from app.domain.exercise.identifiers import ExerciseId
from app.domain.exercise.repository import ExerciseRepository
from app.domain.exercise.value_objects import ExerciseInstructions, ExerciseName
from app.domain.shared_kernel.clock import FixedClock
from app.domain.shared_kernel.events import DomainEvent
from app.domain.user.identifiers import UserId
from app.domain.user.repository import UserRepository
from app.domain.user.user import User
from app.domain.user.value_objects import AuthMethod, Locale, Timezone
from app.domain.workout.identifiers import WorkoutId
from app.domain.workout.repository import WorkoutRepository
from app.domain.workout.value_objects import WorkoutDate, WorkoutName
from app.domain.workout.workout import Workout
from app.domain.workout_session.identifiers import WorkoutSessionId
from app.domain.workout_session.repository import WorkoutSessionRepository
from app.domain.workout_session.value_objects import SessionDate
from app.domain.workout_session.workout_session import WorkoutSession

_A_FIXED_INSTANT = datetime(2026, 1, 1, tzinfo=timezone.utc)


def a_fixed_clock() -> FixedClock:
    """A `FixedClock` pinned to an arbitrary, fixed instant — see
    `tests/domain/user/factories.py`'s identical helper."""
    return FixedClock(_A_FIXED_INSTANT)


def a_registered_user() -> User:
    """An Active User — the common "referenced by a Workout" starting
    point most handler tests in this package build on."""
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


def a_planned_workout(*, user_id: UserId | None = None) -> Workout:
    """A freshly planned Workout, events drained — see
    `tests/domain/workout/factories.py`'s identical helper."""
    workout = Workout.plan(
        workout_id=WorkoutId.generate(),
        user_id=user_id or UserId.generate(),
        name=WorkoutName("Push Day"),
        planned_date=WorkoutDate(date(2026, 1, 1)),
        clock=a_fixed_clock(),
    )
    workout.pull_domain_events()
    return workout


def a_planned_session(
    *, workout_id: WorkoutId | None = None, user_id: UserId | None = None
) -> WorkoutSession:
    """A freshly planned WorkoutSession, mirroring
    `tests/domain/workout_session/factories.py`'s identical helper."""
    session = WorkoutSession.plan(
        session_id=WorkoutSessionId.generate(),
        workout_id=workout_id or WorkoutId.generate(),
        user_id=user_id or UserId.generate(),
        session_date=SessionDate(date(2026, 1, 1)),
        clock=a_fixed_clock(),
    )
    session.pull_domain_events()
    return session


def a_created_exercise() -> Exercise:
    """A freshly created, Active Exercise, events drained — mirroring
    `tests/domain/exercise/factories.py`'s identical helper."""
    exercise = Exercise.create(
        exercise_id=ExerciseId.generate(),
        name=ExerciseName("Barbell Bench Press"),
        movement_pattern=MovementPattern.PUSH,
        difficulty=Difficulty.INTERMEDIATE,
        instructions=ExerciseInstructions(
            "Lie on the bench, lower the bar to the chest, press up."
        ),
        clock=a_fixed_clock(),
    )
    exercise.pull_domain_events()
    return exercise


class FakeWorkoutRepository(WorkoutRepository):
    """An in-memory `WorkoutRepository`. `fail_on_get`/`fail_on_add`
    simulate an infrastructure-level failure, matching
    `FakeUserRepository`'s own reasoning."""

    def __init__(
        self,
        workouts: dict[WorkoutId, Workout] | None = None,
        *,
        fail_on_get: bool = False,
        fail_on_add: bool = False,
        fail_on_list: bool = False,
    ) -> None:
        self._workouts: dict[WorkoutId, Workout] = dict(workouts) if workouts else {}
        self.fail_on_get = fail_on_get
        self.fail_on_add = fail_on_add
        self.fail_on_list = fail_on_list
        self.added: list[Workout] = []
        self.removed: list[Workout] = []

    def get(self, entity_id: WorkoutId) -> Workout | None:
        if self.fail_on_get:
            raise RuntimeError("repository unavailable")
        return self._workouts.get(entity_id)

    def add(self, aggregate: Workout) -> None:
        if self.fail_on_add:
            raise ValueError(f"workout {aggregate.id} already exists")
        self.added.append(aggregate)
        self._workouts[aggregate.id] = aggregate

    def remove(self, aggregate: Workout) -> None:
        self.removed.append(aggregate)
        self._workouts.pop(aggregate.id, None)

    def list_by_user(self, user_id: UserId) -> Sequence[Workout]:
        if self.fail_on_list:
            raise RuntimeError("repository unavailable")
        return [workout for workout in self._workouts.values() if workout.user_id == user_id]


class FakeWorkoutSessionRepository(WorkoutSessionRepository):
    """An in-memory `WorkoutSessionRepository`. See
    `FakeWorkoutRepository`'s identical reasoning."""

    def __init__(
        self,
        sessions: dict[WorkoutSessionId, WorkoutSession] | None = None,
        *,
        fail_on_get: bool = False,
        fail_on_add: bool = False,
        fail_on_list: bool = False,
    ) -> None:
        self._sessions: dict[WorkoutSessionId, WorkoutSession] = dict(sessions) if sessions else {}
        self.fail_on_get = fail_on_get
        self.fail_on_add = fail_on_add
        self.fail_on_list = fail_on_list
        self.added: list[WorkoutSession] = []
        self.removed: list[WorkoutSession] = []

    def get(self, entity_id: WorkoutSessionId) -> WorkoutSession | None:
        if self.fail_on_get:
            raise RuntimeError("repository unavailable")
        return self._sessions.get(entity_id)

    def add(self, aggregate: WorkoutSession) -> None:
        if self.fail_on_add:
            raise ValueError(f"workout session {aggregate.id} already exists")
        self.added.append(aggregate)
        self._sessions[aggregate.id] = aggregate

    def remove(self, aggregate: WorkoutSession) -> None:
        self.removed.append(aggregate)
        self._sessions.pop(aggregate.id, None)

    def list_by_user(self, user_id: UserId) -> Sequence[WorkoutSession]:
        if self.fail_on_list:
            raise RuntimeError("repository unavailable")
        return [session for session in self._sessions.values() if session.user_id == user_id]


class FakeExerciseRepository(ExerciseRepository):
    """An in-memory `ExerciseRepository`, lookup-only from this phase's
    handlers' point of view — see `FakeWorkoutRepository`'s identical
    reasoning."""

    def __init__(
        self,
        exercises: dict[ExerciseId, Exercise] | None = None,
        *,
        fail_on_get: bool = False,
    ) -> None:
        self._exercises: dict[ExerciseId, Exercise] = dict(exercises) if exercises else {}
        self.fail_on_get = fail_on_get
        self.added: list[Exercise] = []
        self.removed: list[Exercise] = []

    def get(self, entity_id: ExerciseId) -> Exercise | None:
        if self.fail_on_get:
            raise RuntimeError("repository unavailable")
        return self._exercises.get(entity_id)

    def add(self, aggregate: Exercise) -> None:
        self.added.append(aggregate)
        self._exercises[aggregate.id] = aggregate

    def remove(self, aggregate: Exercise) -> None:
        self.removed.append(aggregate)
        self._exercises.pop(aggregate.id, None)


class FakeUserRepository(UserRepository):
    """An in-memory `UserRepository`, existence-check-only from this
    phase's handlers' point of view — see
    `tests/application/user/factories.py`'s identical fake."""

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
    """An in-memory `UnitOfWork` scoped to up to four fake repositories
    at once — `WorkoutRepository`, `WorkoutSessionRepository`,
    `ExerciseRepository`, `UserRepository` — dispatching
    `get_repository()` by exact requested type. Any repository a given
    test doesn't need defaults to an empty fake of the right type, so a
    single-aggregate test never needs to construct all four explicitly.
    `fail_on_commit` simulates `commit()` itself failing.
    """

    def __init__(
        self,
        *,
        workouts: FakeWorkoutRepository | None = None,
        sessions: FakeWorkoutSessionRepository | None = None,
        exercises: FakeExerciseRepository | None = None,
        users: FakeUserRepository | None = None,
        fail_on_commit: bool = False,
    ) -> None:
        self.workouts = workouts or FakeWorkoutRepository()
        self.sessions = sessions or FakeWorkoutSessionRepository()
        self.exercises = exercises or FakeExerciseRepository()
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
        if repository_type is WorkoutRepository:
            return self.workouts
        if repository_type is WorkoutSessionRepository:
            return self.sessions
        if repository_type is ExerciseRepository:
            return self.exercises
        if repository_type is UserRepository:
            return self.users
        raise KeyError(repository_type)  # pragma: no cover — never exercised, no other repo exists


class RecordingDispatcher(DomainEventDispatcher):
    """A `DomainEventDispatcher` that records every event it was asked
    to dispatch, in order — see
    `tests/application/user/factories.py`'s identical fake."""

    def __init__(self) -> None:
        self.dispatched: list[DomainEvent] = []

    def dispatch(self, events: Sequence[DomainEvent]) -> None:
        self.dispatched.extend(events)


class OrderTrackingDispatcher(DomainEventDispatcher):
    """A `DomainEventDispatcher` that appends `"dispatch"` to a shared
    `call_order` list — paired with `OrderTrackingUnitOfWork`. See
    `tests/application/user/factories.py`'s identical fake."""

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
        workouts: FakeWorkoutRepository | None = None,
        sessions: FakeWorkoutSessionRepository | None = None,
        exercises: FakeExerciseRepository | None = None,
        users: FakeUserRepository | None = None,
        call_order: list[str],
        fail_on_commit: bool = False,
    ) -> None:
        super().__init__(
            workouts=workouts,
            sessions=sessions,
            exercises=exercises,
            users=users,
            fail_on_commit=fail_on_commit,
        )
        self._call_order = call_order

    def commit(self) -> None:
        super().commit()
        self._call_order.append("commit")

    def rollback(self) -> None:
        super().rollback()
        self._call_order.append("rollback")
