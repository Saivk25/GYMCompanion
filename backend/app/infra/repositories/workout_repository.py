"""`WorkoutSqlRepository`: the SQLAlchemy-backed implementation of
`app.domain.workout.repository.WorkoutRepository`.

Tenant scoping shape used by this repository and every other tenant-scoped
repository in this package except `UserSqlRepository` (see that module's
own docstring for why `User` is the one exception):

- `add()`/`remove()` receive the aggregate itself, which already carries
  its own `user_id` — enough information to safely open
  `tenant_scope(session, str(aggregate.user_id))` before touching the row,
  the exact discipline the users-table migration's docstring documents as
  hard-learned (generate the id, scope the tenant, *then* insert).
- `list_by_user(user_id)` receives a `user_id` directly and scopes from it.
- `get(entity_id)` receives only the aggregate's own id, not its owning
  user — there is no way to know which tenant to scope to before the row
  has already been read, and reading it requires the scope to already be
  set. This method therefore does **not** call `tenant_scope` itself; it
  assumes the caller has already entered `tenant_scope(session, ...)` for
  the correct tenant on this session before calling `get()` — the same
  "session-scoped for the duration of one unit of work" pattern
  `tests/infra/test_migrations.py`'s cross-tenant test already
  demonstrates (`with session_factory() as session, tenant_scope(session,
  ...): ...`, then multiple operations inside that one block). A future
  composition root that authenticates a request and opens one
  `tenant_scope` for its duration is expected to be that caller; this
  repository has no substitute mechanism and none is invented here.
"""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select

from app.domain.user.identifiers import UserId
from app.domain.workout.enums import WorkoutStatus
from app.domain.workout.identifiers import WorkoutId
from app.domain.workout.repository import WorkoutRepository
from app.domain.workout.value_objects import (
    WorkoutDate,
    WorkoutDuration,
    WorkoutGoal,
    WorkoutName,
    WorkoutNotes,
)
from app.domain.workout.workout import Workout
from app.infra.database import tenant_scope
from app.infra.models.workout import WorkoutRow
from app.infra.repositories._tracking import TrackingRepository


class WorkoutSqlRepository(WorkoutRepository, TrackingRepository[Workout, WorkoutId, WorkoutRow]):
    """Postgres-backed `WorkoutRepository`. See the module docstring for
    the tenant-scoping shape."""

    def get(self, entity_id: WorkoutId) -> Workout | None:
        row = self._session.get(WorkoutRow, entity_id.value)
        if row is None:
            return None
        workout = _to_domain(row)
        self._track(entity_id, workout, row)
        return workout

    def add(self, aggregate: Workout) -> None:
        with tenant_scope(self._session, str(aggregate.user_id)):
            row = WorkoutRow(workout_id=aggregate.id.value, user_id=aggregate.user_id.value)
            self._apply_to_row(aggregate, row)
            self._session.add(row)
        self._track(aggregate.id, aggregate, row)

    def remove(self, aggregate: Workout) -> None:
        with tenant_scope(self._session, str(aggregate.user_id)):
            row = self._session.get(WorkoutRow, aggregate.id.value)
            if row is not None:
                self._session.delete(row)
        self._untrack(aggregate.id)

    def list_by_user(self, user_id: UserId) -> Sequence[Workout]:
        with tenant_scope(self._session, str(user_id)):
            rows = self._session.scalars(
                select(WorkoutRow).where(WorkoutRow.user_id == user_id.value)
            ).all()
        workouts = []
        for row in rows:
            workout = _to_domain(row)
            self._track(workout.id, workout, row)
            workouts.append(workout)
        return workouts

    def _apply_to_row(self, aggregate: Workout, row: WorkoutRow) -> None:
        row.name = aggregate.name.value
        row.planned_date = aggregate.planned_date.value
        row.planned_at = aggregate.planned_at
        row.status = aggregate.status.value
        row.goal = aggregate.goal.value if aggregate.goal is not None else None
        row.notes = aggregate.notes.value if aggregate.notes is not None else None
        row.duration = aggregate.duration.value if aggregate.duration is not None else None
        row.started_at = aggregate.started_at
        row.completed_at = aggregate.completed_at
        row.cancelled_at = aggregate.cancelled_at


def _to_domain(row: WorkoutRow) -> Workout:
    return Workout(
        WorkoutId(row.workout_id),
        user_id=UserId(row.user_id),
        name=WorkoutName(row.name),
        planned_date=WorkoutDate(row.planned_date),
        planned_at=row.planned_at,
        status=WorkoutStatus(row.status),
        goal=WorkoutGoal(row.goal) if row.goal is not None else None,
        notes=WorkoutNotes(row.notes) if row.notes is not None else None,
        duration=WorkoutDuration(row.duration) if row.duration is not None else None,
        started_at=row.started_at,
        completed_at=row.completed_at,
        cancelled_at=row.cancelled_at,
    )
