"""`ExerciseSqlRepository`: the SQLAlchemy-backed implementation of
`app.domain.exercise.repository.ExerciseRepository`.

No tenant scoping anywhere in this file — `exercises` carries no `user_id`
and no row-level security (see `app/infra/models/exercise.py`'s module
docstring): `Exercise` is a shared, global catalog, not a per-user
aggregate, so there is no tenant to scope to.
"""

from __future__ import annotations

from app.domain.exercise.enums import Difficulty, ExerciseStatus, MovementPattern
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
from app.infra.models.exercise import ExerciseRow
from app.infra.repositories._tracking import TrackingRepository


class ExerciseSqlRepository(
    ExerciseRepository, TrackingRepository[Exercise, ExerciseId, ExerciseRow]
):
    """Postgres-backed `ExerciseRepository`. See the module docstring for
    why no method here touches `tenant_scope`.
    """

    def get(self, entity_id: ExerciseId) -> Exercise | None:
        row = self._session.get(ExerciseRow, entity_id.value)
        if row is None:
            return None
        exercise = _to_domain(row)
        self._track(entity_id, exercise, row)
        return exercise

    def add(self, aggregate: Exercise) -> None:
        row = ExerciseRow(exercise_id=aggregate.id.value)
        self._apply_to_row(aggregate, row)
        self._session.add(row)
        self._track(aggregate.id, aggregate, row)

    def remove(self, aggregate: Exercise) -> None:
        row = self._session.get(ExerciseRow, aggregate.id.value)
        if row is not None:
            self._session.delete(row)
        self._untrack(aggregate.id)

    def _apply_to_row(self, aggregate: Exercise, row: ExerciseRow) -> None:
        row.name = aggregate.name.value
        row.movement_pattern = aggregate.movement_pattern.value
        row.difficulty = aggregate.difficulty.value
        row.instructions = aggregate.instructions.value
        row.description = aggregate.description.value if aggregate.description is not None else None
        row.primary_muscles = [muscle.value for muscle in aggregate.primary_muscles]
        row.secondary_muscles = sorted(aggregate.secondary_muscles.values)
        row.equipment_requirements = sorted(item.value for item in aggregate.equipment_requirements)
        row.contraindication_tags = sorted(aggregate.contraindications.tags)
        row.status = aggregate.status.value
        row.updated_at = aggregate.updated_at
        row.deprecated_at = aggregate.deprecated_at


def _to_domain(row: ExerciseRow) -> Exercise:
    return Exercise(
        ExerciseId(row.exercise_id),
        name=ExerciseName(row.name),
        movement_pattern=MovementPattern(row.movement_pattern),
        difficulty=Difficulty(row.difficulty),
        instructions=ExerciseInstructions(row.instructions),
        created_at=row.created_at,
        description=ExerciseDescription(row.description) if row.description is not None else None,
        primary_muscles=tuple(PrimaryMuscle(value) for value in row.primary_muscles),
        secondary_muscles=SecondaryMuscles(frozenset(row.secondary_muscles)),
        equipment_requirements=frozenset(
            EquipmentRequirement(value) for value in row.equipment_requirements
        ),
        contraindications=Contraindications(frozenset(row.contraindication_tags)),
        status=ExerciseStatus(row.status),
        updated_at=row.updated_at,
        deprecated_at=row.deprecated_at,
    )
