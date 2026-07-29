"""`WorkoutContext`: a read-only snapshot of a Workout for domain services.

Same purpose as `app.domain.user.context.UserContext`: lets a future domain
service — most immediately the Bible's Workout Rules engine (Section 10.1:
"Governs plan generation, volume, and substitution — fully deterministic")
— consume everything it needs to know about one workout in a single
immutable value, without depending on the mutable `Workout` aggregate
directly or being handed a live `Repository` to query mid-calculation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.domain.shared_kernel.value_object import ValueObject
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
    # Import only for the type checker — see UserContext's identical note
    # for why this avoids a real circular import at module load time.
    from app.domain.workout.workout import Workout


@dataclass(frozen=True, kw_only=True)
class WorkoutContext(ValueObject):
    """An immutable snapshot of one Workout, taken at a point in time."""

    workout_id: WorkoutId
    user_id: UserId
    status: WorkoutStatus
    name: WorkoutName
    planned_date: WorkoutDate
    goal: WorkoutGoal | None
    notes: WorkoutNotes | None
    duration: WorkoutDuration | None

    @classmethod
    def from_workout(cls, workout: Workout) -> WorkoutContext:
        """Builds a snapshot from a live `Workout` aggregate. One-
        directional on purpose: `Workout` does not know this type exists.
        """
        return cls(
            workout_id=workout.id,
            user_id=workout.user_id,
            status=workout.status,
            name=workout.name,
            planned_date=workout.planned_date,
            goal=workout.goal,
            notes=workout.notes,
            duration=workout.duration,
        )
