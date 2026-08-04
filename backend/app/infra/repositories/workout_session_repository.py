"""`WorkoutSessionSqlRepository`: the SQLAlchemy-backed implementation of
`app.domain.workout_session.repository.WorkoutSessionRepository`.

The one repository in this package spanning more than one table: per
`docs/adr/0009-exercise-performance-owned-entity.md`, `ExercisePerformance`
and `ExerciseSet` are child objects of `WorkoutSession`, not separate
aggregates, so they persist as `exercise_performances`/`exercise_sets`
(`app/infra/models/workout_session.py`) and are mapped/reconstructed
entirely here — nowhere else. `_SessionRows` bundles the three tables' worth
of already-session-attached rows one `WorkoutSession` maps to, so
`TrackingRepository`'s generic `TId -> (aggregate, row)` tracking (see that
module's docstring) works unchanged even though "row" here means three
tables' worth of rows, not one.

Reconciliation on every write (`add()`, and the flush-time sync
`TrackingRepository` triggers automatically after a mutation like
`WorkoutSession.add_exercise()`/`remove_exercise()`/`log_set()`) diffs the
aggregate's *current* `exercise_performances`/nested `sets` against the
previously known rows: performances no longer present are deleted (their
sets first, to satisfy the `exercise_sets` -> `exercise_performances`
foreign key), new ones are inserted, and existing ones are updated in
place. Sets are never individually removed — `ExercisePerformance` exposes
no such method (only `add_set()`/`complete_set()`) — so reconciliation only
ever adds or updates a set row, never deletes one.

See `workout_repository.py`'s module docstring for the tenant-scoping shape
(`add()`/`remove()`/`list_by_user()` self-scope from a `user_id` they
already have; `get()` trusts the caller to have already opened
`tenant_scope` on the session) — identical here, with `user_id` denormalized
onto every one of the three tables for exactly that reason.
"""

from __future__ import annotations

import uuid
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass, field

from sqlalchemy import select

from app.domain.exercise.identifiers import ExerciseId
from app.domain.user.identifiers import UserId
from app.domain.workout.identifiers import WorkoutId
from app.domain.workout_session.enums import SessionStatus
from app.domain.workout_session.exercise_performance import ExercisePerformance, PerformanceNotes
from app.domain.workout_session.exercise_set import (
    ExerciseSet,
    SetNumber,
    SetReps,
    SetRPE,
    SetWeight,
)
from app.domain.workout_session.identifiers import ExercisePerformanceId, WorkoutSessionId
from app.domain.workout_session.repository import WorkoutSessionRepository
from app.domain.workout_session.value_objects import (
    CompletionPercentage,
    SessionDate,
    SessionDuration,
    SessionNotes,
    SessionRating,
)
from app.domain.workout_session.workout_session import WorkoutSession
from app.infra.database import tenant_scope
from app.infra.models.workout_session import (
    ExercisePerformanceRow,
    ExerciseSetRow,
    WorkoutSessionRow,
)
from app.infra.repositories._tracking import TrackingRepository


@dataclass
class _SessionRows:
    """Every row `WorkoutSessionSqlRepository` has loaded or written for one
    `WorkoutSession`, keyed the same way the aggregate itself is: by
    `performance_id` and `(performance_id, set_number)`. See the module
    docstring."""

    session_row: WorkoutSessionRow
    performance_rows: dict[uuid.UUID, ExercisePerformanceRow] = field(default_factory=dict)
    set_rows: dict[tuple[uuid.UUID, int], ExerciseSetRow] = field(default_factory=dict)


class WorkoutSessionSqlRepository(
    WorkoutSessionRepository,
    TrackingRepository[WorkoutSession, WorkoutSessionId, _SessionRows],
):
    """Postgres-backed `WorkoutSessionRepository`. See the module docstring
    for the multi-table reconciliation shape."""

    def get(self, entity_id: WorkoutSessionId) -> WorkoutSession | None:
        session_row = self._session.get(WorkoutSessionRow, entity_id.value)
        if session_row is None:
            return None

        performance_rows = list(
            self._session.scalars(
                select(ExercisePerformanceRow)
                .where(ExercisePerformanceRow.session_id == entity_id.value)
                .order_by(ExercisePerformanceRow.sequence)
            ).all()
        )
        performance_ids = [row.performance_id for row in performance_rows]
        set_rows = (
            list(
                self._session.scalars(
                    select(ExerciseSetRow)
                    .where(ExerciseSetRow.performance_id.in_(performance_ids))
                    .order_by(ExerciseSetRow.set_number)
                ).all()
            )
            if performance_ids
            else []
        )
        sets_by_performance = _group_sets_by_performance(set_rows)

        workout_session = _to_domain(session_row, performance_rows, sets_by_performance)
        rows = _SessionRows(
            session_row=session_row,
            performance_rows={row.performance_id: row for row in performance_rows},
            set_rows={(row.performance_id, row.set_number): row for row in set_rows},
        )
        self._track(entity_id, workout_session, rows)
        return workout_session

    def add(self, aggregate: WorkoutSession) -> None:
        with tenant_scope(self._session, str(aggregate.user_id)):
            session_row = WorkoutSessionRow(
                session_id=aggregate.id.value,
                workout_id=aggregate.workout_id.value,
                user_id=aggregate.user_id.value,
            )
            self._session.add(session_row)
            rows = _SessionRows(session_row=session_row)
            self._apply_to_row(aggregate, rows)
        self._track(aggregate.id, aggregate, rows)

    def remove(self, aggregate: WorkoutSession) -> None:
        with tenant_scope(self._session, str(aggregate.user_id)):
            performance_rows = self._session.scalars(
                select(ExercisePerformanceRow).where(
                    ExercisePerformanceRow.session_id == aggregate.id.value
                )
            ).all()
            for performance_row in performance_rows:
                set_rows = self._session.scalars(
                    select(ExerciseSetRow).where(
                        ExerciseSetRow.performance_id == performance_row.performance_id
                    )
                ).all()
                for set_row in set_rows:
                    self._session.delete(set_row)
                self._session.delete(performance_row)
            session_row = self._session.get(WorkoutSessionRow, aggregate.id.value)
            if session_row is not None:
                self._session.delete(session_row)
        self._untrack(aggregate.id)

    def list_by_user(self, user_id: UserId) -> Sequence[WorkoutSession]:
        with tenant_scope(self._session, str(user_id)):
            session_rows = list(
                self._session.scalars(
                    select(WorkoutSessionRow).where(WorkoutSessionRow.user_id == user_id.value)
                ).all()
            )
            session_ids = [row.session_id for row in session_rows]
            performance_rows = (
                list(
                    self._session.scalars(
                        select(ExercisePerformanceRow)
                        .where(ExercisePerformanceRow.session_id.in_(session_ids))
                        .order_by(ExercisePerformanceRow.sequence)
                    ).all()
                )
                if session_ids
                else []
            )
            performance_ids = [row.performance_id for row in performance_rows]
            set_rows = (
                list(
                    self._session.scalars(
                        select(ExerciseSetRow)
                        .where(ExerciseSetRow.performance_id.in_(performance_ids))
                        .order_by(ExerciseSetRow.set_number)
                    ).all()
                )
                if performance_ids
                else []
            )

        performances_by_session: dict[uuid.UUID, list[ExercisePerformanceRow]] = defaultdict(list)
        for performance_row in performance_rows:
            performances_by_session[performance_row.session_id].append(performance_row)
        sets_by_performance = _group_sets_by_performance(set_rows)

        sessions = []
        for session_row in session_rows:
            performances_for_session = performances_by_session.get(session_row.session_id, [])
            workout_session = _to_domain(session_row, performances_for_session, sets_by_performance)
            rows = _SessionRows(
                session_row=session_row,
                performance_rows={row.performance_id: row for row in performances_for_session},
                set_rows={
                    (row.performance_id, row.set_number): row
                    for performance_row in performances_for_session
                    for row in sets_by_performance.get(performance_row.performance_id, [])
                },
            )
            self._track(workout_session.id, workout_session, rows)
            sessions.append(workout_session)
        return sessions

    def _apply_to_row(self, aggregate: WorkoutSession, row: _SessionRows) -> None:
        session_row = row.session_row
        session_row.workout_id = aggregate.workout_id.value
        session_row.user_id = aggregate.user_id.value
        session_row.session_date = aggregate.session_date.value
        session_row.planned_at = aggregate.planned_at
        session_row.status = aggregate.status.value
        session_row.notes = aggregate.notes.value
        session_row.duration = aggregate.duration.value if aggregate.duration is not None else None
        session_row.completion_percentage = (
            aggregate.completion_percentage.value
            if aggregate.completion_percentage is not None
            else None
        )
        session_row.rating = aggregate.rating.value if aggregate.rating is not None else None
        session_row.started_at = aggregate.started_at
        session_row.completed_at = aggregate.completed_at
        session_row.abandoned_at = aggregate.abandoned_at

        current_performance_ids = {
            performance.id.value for performance in aggregate.exercise_performances
        }
        for stale_id in set(row.performance_rows) - current_performance_ids:
            for key in [key for key in row.set_rows if key[0] == stale_id]:
                self._session.delete(row.set_rows.pop(key))
            self._session.delete(row.performance_rows.pop(stale_id))

        for sequence, performance in enumerate(aggregate.exercise_performances):
            performance_row = row.performance_rows.get(performance.id.value)
            if performance_row is None:
                performance_row = ExercisePerformanceRow(
                    performance_id=performance.id.value,
                    session_id=aggregate.id.value,
                    user_id=aggregate.user_id.value,
                    exercise_id=performance.exercise_id.value,
                    sequence=sequence,
                    notes=performance.notes.value,
                )
                self._session.add(performance_row)
                row.performance_rows[performance.id.value] = performance_row
            else:
                performance_row.sequence = sequence
                performance_row.notes = performance.notes.value

            for exercise_set in performance.sets:
                key = (performance.id.value, exercise_set.set_number.value)
                set_row = row.set_rows.get(key)
                if set_row is None:
                    set_row = ExerciseSetRow(
                        performance_id=performance.id.value,
                        set_number=exercise_set.set_number.value,
                        user_id=aggregate.user_id.value,
                    )
                    self._session.add(set_row)
                    row.set_rows[key] = set_row
                set_row.weight = exercise_set.weight.value
                set_row.reps = exercise_set.reps.value
                set_row.rpe = exercise_set.rpe.value
                set_row.completed = exercise_set.completed


def _group_sets_by_performance(
    set_rows: Sequence[ExerciseSetRow],
) -> dict[uuid.UUID, list[ExerciseSetRow]]:
    grouped: dict[uuid.UUID, list[ExerciseSetRow]] = defaultdict(list)
    for set_row in set_rows:
        grouped[set_row.performance_id].append(set_row)
    return grouped


def _to_domain(
    session_row: WorkoutSessionRow,
    performance_rows: Sequence[ExercisePerformanceRow],
    sets_by_performance: dict[uuid.UUID, list[ExerciseSetRow]],
) -> WorkoutSession:
    performances = tuple(
        ExercisePerformance(
            ExercisePerformanceId(performance_row.performance_id),
            exercise_id=ExerciseId(performance_row.exercise_id),
            notes=PerformanceNotes(performance_row.notes),
            sets=tuple(
                ExerciseSet(
                    set_number=SetNumber(set_row.set_number),
                    weight=SetWeight(set_row.weight),
                    reps=SetReps(set_row.reps),
                    rpe=SetRPE(set_row.rpe),
                    completed=set_row.completed,
                )
                for set_row in sets_by_performance.get(performance_row.performance_id, [])
            ),
        )
        for performance_row in performance_rows
    )
    return WorkoutSession(
        WorkoutSessionId(session_row.session_id),
        workout_id=WorkoutId(session_row.workout_id),
        user_id=UserId(session_row.user_id),
        session_date=SessionDate(session_row.session_date),
        planned_at=session_row.planned_at,
        status=SessionStatus(session_row.status),
        notes=SessionNotes(session_row.notes),
        duration=SessionDuration(session_row.duration)
        if session_row.duration is not None
        else None,
        completion_percentage=(
            CompletionPercentage(session_row.completion_percentage)
            if session_row.completion_percentage is not None
            else None
        ),
        rating=SessionRating(session_row.rating) if session_row.rating is not None else None,
        started_at=session_row.started_at,
        completed_at=session_row.completed_at,
        abandoned_at=session_row.abandoned_at,
        exercise_performances=performances,
    )
