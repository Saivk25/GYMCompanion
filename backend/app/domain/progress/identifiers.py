"""The Progress aggregate's typed identifier.

Same pattern as `app.domain.user.identifiers.UserId`,
`app.domain.workout.identifiers.WorkoutId`,
`app.domain.exercise.identifiers.ExerciseId`, and
`app.domain.workout_session.identifiers.WorkoutSessionId` — a thin
subclass of the shared kernel's `EntityId` so mypy treats a `ProgressId` as
distinct from every other aggregate's id, at zero runtime cost.
"""

from __future__ import annotations

from app.domain.shared_kernel.identifiers import EntityId


class ProgressId(EntityId):
    """Strongly-typed identifier for the Progress aggregate root."""
