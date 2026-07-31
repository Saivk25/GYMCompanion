"""`WorkoutDTO`: the read-only projection of a `Workout` aggregate
returned to whatever calls a Workout query handler.

**Not the same type as `app.domain.workout.context.WorkoutContext`,
deliberately** — the same reasoning
`app.application.user.dto.user_dto.UserDTO`'s own module docstring
gives for not reusing `app.domain.user.context.UserContext`:
`WorkoutContext` is scoped to a future domain service (the Bible's
Workout Rules engine), one-directional, and never crosses the
Application Layer boundary; `WorkoutDTO` is this layer's own read
projection for `GetWorkoutHandler`/`ListWorkoutsHandler`, a different
consumer with different reasons to change independently. See
`docs/adr/0024-workout-application-use-cases.md`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from app.domain.user.identifiers import UserId
from app.domain.workout.enums import WorkoutStatus
from app.domain.workout.identifiers import WorkoutId
from app.domain.workout.value_objects import (
    WorkoutDate,
    WorkoutDuration,
    WorkoutGoal,
    WorkoutName,
    WorkoutNotes,
)

if TYPE_CHECKING:
    # Import only for the type checker — see UserDTO's identical note
    # for why this avoids a real circular import at module load time.
    from app.domain.workout.workout import Workout


@dataclass(frozen=True, kw_only=True)
class WorkoutDTO:
    """An immutable, read-only snapshot of one `Workout`, taken at
    query time."""

    workout_id: WorkoutId
    user_id: UserId
    status: WorkoutStatus
    name: WorkoutName
    planned_date: WorkoutDate
    planned_at: datetime
    goal: WorkoutGoal | None
    notes: WorkoutNotes | None
    duration: WorkoutDuration | None
    started_at: datetime | None
    completed_at: datetime | None
    cancelled_at: datetime | None

    @classmethod
    def from_workout(cls, workout: Workout) -> WorkoutDTO:
        """Builds a DTO from a live `Workout` aggregate. One-directional
        on purpose, mirroring `UserDTO.from_user` — `Workout` never
        depends on this type.
        """
        return cls(
            workout_id=workout.id,
            user_id=workout.user_id,
            status=workout.status,
            name=workout.name,
            planned_date=workout.planned_date,
            planned_at=workout.planned_at,
            goal=workout.goal,
            notes=workout.notes,
            duration=workout.duration,
            started_at=workout.started_at,
            completed_at=workout.completed_at,
            cancelled_at=workout.cancelled_at,
        )
