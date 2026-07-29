"""The Exercise aggregate's typed identifier.

Same pattern as `app.domain.user.identifiers.UserId` and
`app.domain.workout.identifiers.WorkoutId` — a thin subclass of the shared
kernel's `EntityId` so mypy treats an `ExerciseId` as distinct from every
other aggregate's id, at zero runtime cost.
"""

from __future__ import annotations

from app.domain.shared_kernel.identifiers import EntityId


class ExerciseId(EntityId):
    """Strongly-typed identifier for the Exercise aggregate root."""
