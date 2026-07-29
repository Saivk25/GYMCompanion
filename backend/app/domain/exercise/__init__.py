"""The Exercise aggregate: Sprint 2's third real aggregate, built on the
Sprint 1 shared kernel (`app.domain.shared_kernel`) and following the same
pattern as `app.domain.user` and `app.domain.workout`. Training bounded
context (Domain Model & Decision Engine Bible, Section 3, Table 2), closest
deep dive in Section 4.5 (`ExerciseGraph`).

Scope of this first increment — deliberately smaller than the Bible's
`ExerciseGraph`, not an oversight: this is the `Exercise` node only, with
no `ExerciseRelation` (progression/regression/substitute/antagonist-pair/
accessory-of), no graph traversal, and no AI recommendation layer. Every
`Exercise` also stands alone from `Workout`: no set-logging relationship
exists yet. See `docs/adr/0007-exercise-aggregate-first-increment.md` for
the full reasoning, including why `Exercise` — unlike `User` and
`Workout` — carries no `user_id`: it is a shared, global catalog entity,
not a per-tenant one.

Depends on nothing outside the Python standard library and
`app.domain.shared_kernel` — enforced by the same statically-checked rule
as the rest of `app/domain` (`tests/domain/test_import_boundaries.py`).
Unlike `app.domain.workout` (which references `app.domain.user.UserId` for
its owning tenant), `Exercise` has no such reference: it belongs to no
aggregate and is owned by none.
"""

from app.domain.exercise.context import ExerciseContext
from app.domain.exercise.enums import Difficulty, ExerciseStatus, MovementPattern
from app.domain.exercise.events import ExerciseCreated, ExerciseDeprecated, ExerciseUpdated
from app.domain.exercise.exercise import Exercise
from app.domain.exercise.identifiers import ExerciseId
from app.domain.exercise.repository import ExerciseRepository
from app.domain.exercise.value_objects import (
    Contraindications,
    EquipmentRequirement,
    ExerciseDescription,
    ExerciseInstructions,
    ExerciseName,
    PrimaryMuscle,
    SecondaryMuscles,
)

__all__ = [
    "Contraindications",
    "Difficulty",
    "EquipmentRequirement",
    "Exercise",
    "ExerciseContext",
    "ExerciseCreated",
    "ExerciseDeprecated",
    "ExerciseDescription",
    "ExerciseId",
    "ExerciseInstructions",
    "ExerciseName",
    "ExerciseRepository",
    "ExerciseStatus",
    "ExerciseUpdated",
    "MovementPattern",
    "PrimaryMuscle",
    "SecondaryMuscles",
]
