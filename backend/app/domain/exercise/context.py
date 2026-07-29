"""`ExerciseContext`: a read-only snapshot of an Exercise for domain
services.

Same purpose as `app.domain.user.context.UserContext` and
`app.domain.workout.context.WorkoutContext`: lets a future domain service —
most immediately the Bible's Safety Rules (checking `contraindications`
against a user's active safety flags) and Substitution/Plan-generation
logic (checking `equipment_requirements` against an `EnvironmentContext`,
neither built yet) — consume everything it needs to know about one
exercise in a single immutable value.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.domain.exercise.enums import Difficulty, ExerciseStatus, MovementPattern
from app.domain.exercise.identifiers import ExerciseId
from app.domain.exercise.value_objects import (
    Contraindications,
    EquipmentRequirement,
    ExerciseName,
    PrimaryMuscle,
    SecondaryMuscles,
)
from app.domain.shared_kernel.value_object import ValueObject

if TYPE_CHECKING:
    # Import only for the type checker — see UserContext's identical note
    # for why this avoids a real circular import at module load time.
    from app.domain.exercise.exercise import Exercise


@dataclass(frozen=True, kw_only=True)
class ExerciseContext(ValueObject):
    """An immutable snapshot of one Exercise, taken at a point in time."""

    exercise_id: ExerciseId
    status: ExerciseStatus
    name: ExerciseName
    movement_pattern: MovementPattern
    difficulty: Difficulty
    primary_muscles: tuple[PrimaryMuscle, ...]
    secondary_muscles: SecondaryMuscles
    equipment_requirements: frozenset[EquipmentRequirement]
    contraindications: Contraindications

    @classmethod
    def from_exercise(cls, exercise: Exercise) -> ExerciseContext:
        """Builds a snapshot from a live `Exercise` aggregate. One-
        directional on purpose: `Exercise` does not know this type exists.
        """
        return cls(
            exercise_id=exercise.id,
            status=exercise.status,
            name=exercise.name,
            movement_pattern=exercise.movement_pattern,
            difficulty=exercise.difficulty,
            primary_muscles=exercise.primary_muscles,
            secondary_muscles=exercise.secondary_muscles,
            equipment_requirements=exercise.equipment_requirements,
            contraindications=exercise.contraindications,
        )
