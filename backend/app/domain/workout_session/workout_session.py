"""The WorkoutSession aggregate root.

The execution record of a workout: `Workout` (`app.domain.workout`) is the
plan or intention — what should happen; `WorkoutSession` is what actually
happened when a user acted on it. See
`docs/adr/0008-workout-session-execution-record.md` for the full reasoning
behind this split and how it relates to the Domain Model & Decision Engine
Bible's own `WorkoutSession` (Section 4.7). Built entirely on the Sprint 1
shared kernel (`app.domain.shared_kernel`), following the same pattern as
`app.domain.user.User`, `app.domain.workout.Workout`, and
`app.domain.exercise.Exercise`.

Tenant-scoped like `Workout` (carries `user_id`), and additionally
references the `Workout` it executes (`workout_id`) — an aggregate
referencing two other aggregates, both by id only, never by object
reference, the same discipline `Workout.user_id` already established.

Sprint 2 Step 5 adds `ExercisePerformance`/`ExerciseSet` (`exercise_
performance.py`/`exercise_set.py`) as entities/value objects owned by this
aggregate — what the user actually performed, exercise by exercise, set by
set. See `docs/adr/0009-exercise-performance-owned-entity.md` for why they
live here instead of as a separate aggregate with its own repository.
Every mutating method that touches an `ExercisePerformance` or
`ExerciseSet` goes through `_ensure_mutable()` below: "cannot modify sets
once the session is Completed or Abandoned" can only be enforced here,
since neither child object has any visibility into this aggregate's own
`_status` — the same "the aggregate root enforces what no single child can
see" reasoning `app.domain.exercise.exercise`'s muscle-overlap check
already established for cross-field invariants.
"""

from __future__ import annotations

from datetime import datetime

from app.domain.exercise.identifiers import ExerciseId
from app.domain.shared_kernel.aggregate_root import AggregateRoot
from app.domain.shared_kernel.clock import Clock
from app.domain.shared_kernel.errors import DomainInvariantViolationError
from app.domain.shared_kernel.validation import ensure
from app.domain.user.identifiers import UserId
from app.domain.workout.identifiers import WorkoutId
from app.domain.workout_session.enums import SessionStatus
from app.domain.workout_session.events import (
    ExerciseAddedToSession,
    ExercisePerformanceUpdated,
    ExerciseRemovedFromSession,
    ExerciseSetCompleted,
    WorkoutSessionAbandoned,
    WorkoutSessionCompleted,
    WorkoutSessionNotesUpdated,
    WorkoutSessionStarted,
)
from app.domain.workout_session.exercise_performance import ExercisePerformance, PerformanceNotes
from app.domain.workout_session.exercise_set import ExerciseSet
from app.domain.workout_session.identifiers import ExercisePerformanceId, WorkoutSessionId
from app.domain.workout_session.value_objects import (
    CompletionPercentage,
    SessionDate,
    SessionDuration,
    SessionNotes,
    SessionRating,
)

# Same table-driven technique as User's AccountStatus, Workout's
# WorkoutStatus, and Exercise's ExerciseStatus: Completed and Abandoned
# both map to an empty allowed set, which is what makes "cannot start
# twice", "cannot complete twice", and "cannot abandon after completion"
# all true by construction.
_ALLOWED_TRANSITIONS: dict[SessionStatus, frozenset[SessionStatus]] = {
    SessionStatus.PLANNED: frozenset({SessionStatus.ACTIVE, SessionStatus.ABANDONED}),
    SessionStatus.ACTIVE: frozenset({SessionStatus.COMPLETED, SessionStatus.ABANDONED}),
    SessionStatus.COMPLETED: frozenset(),
    SessionStatus.ABANDONED: frozenset(),
}


class WorkoutSession(AggregateRoot[WorkoutSessionId]):
    """The WorkoutSession aggregate. See the module docstring for how this
    relates to `Workout`.

    Construct a brand-new session via the `plan()` factory, never
    `WorkoutSession(...)` directly — the constructor is also used to
    rehydrate an existing session from a repository. Unlike
    `User.register()`/`Workout.plan()`/`Exercise.create()`, `plan()` here
    raises no event — see `events.py`'s module docstring for why.
    """

    def __init__(
        self,
        session_id: WorkoutSessionId,
        *,
        workout_id: WorkoutId,
        user_id: UserId,
        session_date: SessionDate,
        planned_at: datetime,
        status: SessionStatus = SessionStatus.PLANNED,
        notes: SessionNotes | None = None,
        duration: SessionDuration | None = None,
        completion_percentage: CompletionPercentage | None = None,
        rating: SessionRating | None = None,
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
        abandoned_at: datetime | None = None,
        exercise_performances: tuple[ExercisePerformance, ...] = (),
    ) -> None:
        super().__init__(session_id)
        ensure(planned_at.tzinfo is not None, "planned_at must be timezone-aware")
        self._workout_id = workout_id
        self._user_id = user_id
        self._session_date = session_date
        self._planned_at = planned_at
        self._status = status
        self._notes = notes if notes is not None else SessionNotes()
        self._duration = duration
        self._completion_percentage = completion_percentage
        self._rating = rating
        self._started_at = started_at
        self._completed_at = completed_at
        self._abandoned_at = abandoned_at
        self._exercise_performances = exercise_performances

    @classmethod
    def plan(
        cls,
        *,
        session_id: WorkoutSessionId,
        workout_id: WorkoutId,
        user_id: UserId,
        session_date: SessionDate,
        clock: Clock,
    ) -> WorkoutSession:
        """Creates a brand-new WorkoutSession in the Planned state.
        `session_id` is generated by the caller (`WorkoutSessionId.
        generate()`) before calling this — the same convention every
        other aggregate's factory follows. Raises no event; see the class
        docstring for why.
        """
        return cls(
            session_id,
            workout_id=workout_id,
            user_id=user_id,
            session_date=session_date,
            planned_at=clock.now(),
        )

    @property
    def workout_id(self) -> WorkoutId:
        return self._workout_id

    @property
    def user_id(self) -> UserId:
        return self._user_id

    @property
    def session_date(self) -> SessionDate:
        return self._session_date

    @property
    def planned_at(self) -> datetime:
        return self._planned_at

    @property
    def status(self) -> SessionStatus:
        return self._status

    @property
    def notes(self) -> SessionNotes:
        return self._notes

    @property
    def duration(self) -> SessionDuration | None:
        return self._duration

    @property
    def completion_percentage(self) -> CompletionPercentage | None:
        return self._completion_percentage

    @property
    def rating(self) -> SessionRating | None:
        return self._rating

    @property
    def started_at(self) -> datetime | None:
        return self._started_at

    @property
    def completed_at(self) -> datetime | None:
        return self._completed_at

    @property
    def abandoned_at(self) -> datetime | None:
        return self._abandoned_at

    @property
    def exercise_performances(self) -> tuple[ExercisePerformance, ...]:
        """Every `ExercisePerformance` logged in this session, in the order
        they were added."""
        return self._exercise_performances

    def update_notes(self, notes: SessionNotes, *, clock: Clock) -> None:
        """Replaces the session's notes and records
        `WorkoutSessionNotesUpdated`.

        Deliberately not blocked once Completed or Abandoned — contrast
        `Workout.update_notes`/`Exercise.update`, both of which reject any
        edit once terminal. The Domain Model & Decision Engine Bible says
        the opposite for the real `WorkoutSession`: "Immutable once
        Completed; corrections are appended as a note, never an overwrite"
        (Section 4.7, Table 10, "Versioning") — a correction *after*
        completion is the expected case, not a forbidden one. This
        increment doesn't yet implement true append-only history (that's
        deferred, see the ADR); it allows the replace unconditionally
        rather than silently contradicting the Bible by blocking it.
        """
        self._notes = notes
        self.record_event(
            WorkoutSessionNotesUpdated(occurred_at=clock.now(), session_id=self.id, notes=notes)
        )

    def start(self, *, clock: Clock) -> None:
        """Planned -> Active."""
        self._transition_to(SessionStatus.ACTIVE)
        self._started_at = clock.now()
        self.record_event(
            WorkoutSessionStarted(
                occurred_at=self._started_at,
                session_id=self.id,
                workout_id=self._workout_id,
                user_id=self._user_id,
            )
        )

    def complete(
        self,
        *,
        duration: SessionDuration,
        completion_percentage: CompletionPercentage,
        rating: SessionRating | None = None,
        clock: Clock,
    ) -> None:
        """Active -> Completed. `duration` and `completion_percentage` are
        required — a completed session always has a recorded elapsed time
        and a recorded completion share, even if that share is 100.
        `rating` is optional: a user may finish a session without rating
        it.
        """
        self._transition_to(SessionStatus.COMPLETED)
        self._completed_at = clock.now()
        self._duration = duration
        self._completion_percentage = completion_percentage
        self._rating = rating
        self.record_event(
            WorkoutSessionCompleted(
                occurred_at=self._completed_at,
                session_id=self.id,
                workout_id=self._workout_id,
                user_id=self._user_id,
                duration=duration,
                completion_percentage=completion_percentage,
            )
        )

    def abandon(
        self,
        *,
        clock: Clock,
        duration: SessionDuration | None = None,
        completion_percentage: CompletionPercentage | None = None,
    ) -> None:
        """Planned -> Abandoned, or Active -> Abandoned. `duration`/
        `completion_percentage` are optional here, unlike `complete()`: an
        abandoned session may have nothing meaningful logged (abandoned
        before ever starting) or a partial record worth keeping (abandoned
        partway through) — both are legitimate.
        """
        self._transition_to(SessionStatus.ABANDONED)
        self._abandoned_at = clock.now()
        if duration is not None:
            self._duration = duration
        if completion_percentage is not None:
            self._completion_percentage = completion_percentage
        self.record_event(
            WorkoutSessionAbandoned(
                occurred_at=self._abandoned_at,
                session_id=self.id,
                workout_id=self._workout_id,
                user_id=self._user_id,
            )
        )

    def _transition_to(self, target: SessionStatus) -> None:
        allowed = _ALLOWED_TRANSITIONS[self._status]
        ensure(
            target in allowed,
            f"cannot transition workout session status from "
            f"{self._status.value!r} to {target.value!r}",
        )
        self._status = target

    def add_exercise(
        self,
        exercise_id: ExerciseId,
        *,
        clock: Clock,
        notes: PerformanceNotes | None = None,
    ) -> ExercisePerformanceId:
        """Starts logging a new exercise within this session, returning the
        new `ExercisePerformance`'s id. `exercise_id` is a typed reference
        only — no lookup against `app.domain.exercise` is performed or
        implied; whether it names a real, still-`Active` `Exercise` is the
        caller's (application layer's) responsibility, per this task's own
        "typed reference only; no repository lookup" instruction.
        """
        self._ensure_mutable()
        performance_id = ExercisePerformanceId.generate()
        performance = ExercisePerformance(performance_id, exercise_id=exercise_id, notes=notes)
        self._exercise_performances = (*self._exercise_performances, performance)
        self.record_event(
            ExerciseAddedToSession(
                occurred_at=clock.now(),
                session_id=self.id,
                performance_id=performance_id,
                exercise_id=exercise_id,
            )
        )
        return performance_id

    def remove_exercise(self, performance_id: ExercisePerformanceId, *, clock: Clock) -> None:
        """Removes a previously added `ExercisePerformance` and every set
        logged on it."""
        self._ensure_mutable()
        performance = self._find_performance(performance_id)
        self._exercise_performances = tuple(
            existing for existing in self._exercise_performances if existing.id != performance_id
        )
        self.record_event(
            ExerciseRemovedFromSession(
                occurred_at=clock.now(),
                session_id=self.id,
                performance_id=performance_id,
                exercise_id=performance.exercise_id,
            )
        )

    def log_set(
        self,
        performance_id: ExercisePerformanceId,
        exercise_set: ExerciseSet,
        *,
        clock: Clock,
    ) -> None:
        """Appends a newly logged `ExerciseSet` to the named performance.
        Duplicate `set_number`s are rejected by `ExercisePerformance.
        add_set()` itself; this method's own job is only the "session
        isn't Completed/Abandoned" and "performance exists" guards.
        """
        self._ensure_mutable()
        performance = self._find_performance(performance_id)
        performance.add_set(exercise_set)
        self.record_event(
            ExercisePerformanceUpdated(
                occurred_at=clock.now(),
                session_id=self.id,
                performance_id=performance_id,
                exercise_id=performance.exercise_id,
            )
        )

    def complete_set(
        self,
        performance_id: ExercisePerformanceId,
        set_number: int,
        *,
        clock: Clock,
    ) -> None:
        """Marks the given set number complete on the named performance."""
        self._ensure_mutable()
        performance = self._find_performance(performance_id)
        completed_set = performance.complete_set(set_number)
        self.record_event(
            ExerciseSetCompleted(
                occurred_at=clock.now(),
                session_id=self.id,
                performance_id=performance_id,
                exercise_id=performance.exercise_id,
                exercise_set=completed_set,
            )
        )

    def update_exercise_notes(
        self,
        performance_id: ExercisePerformanceId,
        notes: PerformanceNotes,
        *,
        clock: Clock,
    ) -> None:
        """Replaces the notes on one exercise's performance within this
        session — the `ExercisePerformance`-scoped counterpart to
        `update_notes()`. Also blocked once Completed/Abandoned, unlike
        `update_notes()`: the Bible's "corrections are appended, never
        overwritten" allowance (see that method's docstring) is stated for
        session-level notes specifically, not for what was actually
        performed — the logged sets and per-exercise notes are exactly the
        historical record that allowance protects, so they close along
        with the session rather than staying open for edits after the
        fact.
        """
        self._ensure_mutable()
        performance = self._find_performance(performance_id)
        performance.update_notes(notes)
        self.record_event(
            ExercisePerformanceUpdated(
                occurred_at=clock.now(),
                session_id=self.id,
                performance_id=performance_id,
                exercise_id=performance.exercise_id,
            )
        )

    def _find_performance(self, performance_id: ExercisePerformanceId) -> ExercisePerformance:
        for performance in self._exercise_performances:
            if performance.id == performance_id:
                return performance
        raise DomainInvariantViolationError(
            f"no exercise performance with id {performance_id} on this session"
        )

    def _ensure_mutable(self) -> None:
        """Guards every mutation of `exercise_performances`/`ExerciseSet`s:
        "cannot modify sets once the session is Completed or Abandoned."
        See the class docstring for why this check lives here rather than
        on `ExercisePerformance`/`ExerciseSet` themselves.
        """
        ensure(
            self._status not in (SessionStatus.COMPLETED, SessionStatus.ABANDONED),
            f"cannot modify exercise performances once the workout session "
            f"is {self._status.value!r}",
        )
