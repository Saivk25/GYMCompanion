"""Domain events raised by the Exercise aggregate.

Scoped to exactly the three events this increment's task named —
`ExerciseCreated`, `ExerciseUpdated`, `ExerciseDeprecated` — the same
"raise only what the aggregate's own methods actually do" discipline
`app.domain.user.events` and `app.domain.workout.events` already follow.
"""

from dataclasses import dataclass

from app.domain.exercise.enums import Difficulty, MovementPattern
from app.domain.exercise.identifiers import ExerciseId
from app.domain.exercise.value_objects import ExerciseName
from app.domain.shared_kernel.events import DomainEvent


@dataclass(frozen=True, kw_only=True)
class ExerciseCreated(DomainEvent):
    """A new Exercise was created via `Exercise.create(...)`. Carries
    `movement_pattern` and `difficulty` alongside `name` since a first
    subscriber (a catalog index, a Plan-generation cache) would need them
    immediately without re-fetching the aggregate.
    """

    exercise_id: ExerciseId
    name: ExerciseName
    movement_pattern: MovementPattern
    difficulty: Difficulty


@dataclass(frozen=True, kw_only=True)
class ExerciseUpdated(DomainEvent):
    """`Exercise.update(...)` changed one or more fields. Carries only
    `exercise_id` and the current `name` — a subscriber needing the rest
    of the current state re-fetches via `ExerciseRepository`, the same
    minimal-payload choice `WorkoutCancelled`/`WorkoutStarted` already make.
    """

    exercise_id: ExerciseId
    name: ExerciseName


@dataclass(frozen=True, kw_only=True)
class ExerciseDeprecated(DomainEvent):
    """`Exercise.deprecate(...)` moved the exercise to Deprecated."""

    exercise_id: ExerciseId
