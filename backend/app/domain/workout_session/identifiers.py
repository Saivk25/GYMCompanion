"""The WorkoutSession aggregate's typed identifier.

Same pattern as `app.domain.user.identifiers.UserId`,
`app.domain.workout.identifiers.WorkoutId`, and
`app.domain.exercise.identifiers.ExerciseId` — a thin subclass of the
shared kernel's `EntityId` so mypy treats a `WorkoutSessionId` as distinct
from every other aggregate's id, at zero runtime cost.
"""

from __future__ import annotations

from app.domain.shared_kernel.identifiers import EntityId


class WorkoutSessionId(EntityId):
    """Strongly-typed identifier for the WorkoutSession aggregate root."""
