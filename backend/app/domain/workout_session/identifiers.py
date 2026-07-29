"""Typed identifiers owned by the WorkoutSession aggregate.

Same pattern as `app.domain.user.identifiers.UserId`,
`app.domain.workout.identifiers.WorkoutId`, and
`app.domain.exercise.identifiers.ExerciseId` — a thin subclass of the
shared kernel's `EntityId` so mypy treats each id as distinct from every
other, at zero runtime cost.

`ExercisePerformanceId` identifies `ExercisePerformance` (`exercise_
performance.py`), a *child entity* of this aggregate, not a second
aggregate root — it has no repository of its own (see
`docs/adr/0009-exercise-performance-owned-entity.md`) but still needs a
stable identity distinct from its `set_number`-keyed `ExerciseSet`
children, which are value objects instead (see `exercise_set.py`'s module
docstring for why those two ownership shapes differ).
"""

from __future__ import annotations

from app.domain.shared_kernel.identifiers import EntityId


class WorkoutSessionId(EntityId):
    """Strongly-typed identifier for the WorkoutSession aggregate root."""


class ExercisePerformanceId(EntityId):
    """Strongly-typed identifier for the `ExercisePerformance` entity,
    unique within the `WorkoutSession` that owns it (and, since ids are
    random UUIDs, globally)."""
