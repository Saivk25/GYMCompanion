"""The Exercise aggregate root.

Gym Companion's canonical exercise library: what an exercise *is*, not how
a user performed it — that's `Workout` (and a future `ExerciseSet`, out of
scope here). Domain Model & Decision Engine Bible, Section 4.5's
`ExerciseGraph` is the closest analog, but this increment builds the
`Exercise` node only, with no relationships, no substitution, no
progression/regression — see
`docs/adr/0007-exercise-aggregate-first-increment.md`. Built entirely on
the Sprint 1 shared kernel (`app.domain.shared_kernel`), following the same
pattern as `app.domain.user.User` and `app.domain.workout.Workout`.

Unlike `User` and `Workout`, `Exercise` is not tenant-scoped: it carries no
`user_id`. The Bible is explicit that this aggregate is "curated by the
system/maintainer" and "shared/global, not per-user" (Section 4.5, Table
8, "Ownership"/"Privacy") — every `Exercise` is visible to every user, the
same way a paper exercise encyclopedia doesn't belong to any one reader.
"""

from __future__ import annotations

from datetime import datetime

from app.domain.exercise.enums import Difficulty, ExerciseStatus, MovementPattern
from app.domain.exercise.events import ExerciseCreated, ExerciseDeprecated, ExerciseUpdated
from app.domain.exercise.identifiers import ExerciseId
from app.domain.exercise.value_objects import (
    Contraindications,
    EquipmentRequirement,
    ExerciseDescription,
    ExerciseInstructions,
    ExerciseName,
    PrimaryMuscle,
    SecondaryMuscles,
)
from app.domain.shared_kernel.aggregate_root import AggregateRoot
from app.domain.shared_kernel.clock import Clock
from app.domain.shared_kernel.validation import ensure

# Same table-driven technique as User's AccountStatus and Workout's
# WorkoutStatus, applied to a smaller graph: Active -> Deprecated,
# one-directional and terminal. Deprecated's empty set is what makes
# "cannot deprecate a deprecated exercise" true by construction rather
# than a separate guard clause.
_ALLOWED_TRANSITIONS: dict[ExerciseStatus, frozenset[ExerciseStatus]] = {
    ExerciseStatus.ACTIVE: frozenset({ExerciseStatus.DEPRECATED}),
    ExerciseStatus.DEPRECATED: frozenset(),
}


def _ensure_no_muscle_overlap(
    primary_muscles: tuple[PrimaryMuscle, ...],
    secondary_muscles: SecondaryMuscles,
) -> None:
    """The one invariant no single value object can enforce on its own:
    checking `primary_muscles` doesn't require reading `secondary_muscles`
    and vice versa, so this can only live on the aggregate that holds both.
    Called from `__init__` (construction) and `update()` (after applying
    whichever fields changed), so it's impossible to reach an invalid
    combination through either path.
    """
    primary_values = tuple(muscle.value for muscle in primary_muscles)
    ensure(
        len(primary_values) == len(set(primary_values)),
        f"primary_muscles must not contain a duplicate muscle, got {primary_values}",
    )
    overlap = set(primary_values) & secondary_muscles.values
    ensure(
        not overlap,
        f"a muscle cannot be both primary and secondary, got overlap: {sorted(overlap)}",
    )


class Exercise(AggregateRoot[ExerciseId]):
    """The Exercise aggregate. See the module docstring for scope and the
    ADR for how this relates to the Bible's `ExerciseGraph`.

    Construct a brand-new exercise via the `create()` factory, never
    `Exercise(...)` directly — the constructor is also used to rehydrate an
    existing exercise from a repository, where re-raising `ExerciseCreated`
    would be wrong. See `create()`, and `app.domain.user.User` for the same
    pattern explained in more depth.
    """

    def __init__(
        self,
        exercise_id: ExerciseId,
        *,
        name: ExerciseName,
        movement_pattern: MovementPattern,
        difficulty: Difficulty,
        instructions: ExerciseInstructions,
        created_at: datetime,
        description: ExerciseDescription | None = None,
        primary_muscles: tuple[PrimaryMuscle, ...] = (),
        secondary_muscles: SecondaryMuscles | None = None,
        equipment_requirements: frozenset[EquipmentRequirement] = frozenset(),
        contraindications: Contraindications | None = None,
        status: ExerciseStatus = ExerciseStatus.ACTIVE,
        updated_at: datetime | None = None,
        deprecated_at: datetime | None = None,
    ) -> None:
        super().__init__(exercise_id)
        ensure(created_at.tzinfo is not None, "created_at must be timezone-aware")
        resolved_secondary_muscles = secondary_muscles or SecondaryMuscles()
        _ensure_no_muscle_overlap(primary_muscles, resolved_secondary_muscles)
        self._name = name
        self._movement_pattern = movement_pattern
        self._difficulty = difficulty
        self._instructions = instructions
        self._created_at = created_at
        self._description = description
        self._primary_muscles = primary_muscles
        self._secondary_muscles = resolved_secondary_muscles
        self._equipment_requirements = equipment_requirements
        self._contraindications = contraindications or Contraindications()
        self._status = status
        self._updated_at = updated_at
        self._deprecated_at = deprecated_at

    @classmethod
    def create(
        cls,
        *,
        exercise_id: ExerciseId,
        name: ExerciseName,
        movement_pattern: MovementPattern,
        difficulty: Difficulty,
        instructions: ExerciseInstructions,
        description: ExerciseDescription | None = None,
        primary_muscles: tuple[PrimaryMuscle, ...] = (),
        secondary_muscles: SecondaryMuscles | None = None,
        equipment_requirements: frozenset[EquipmentRequirement] = frozenset(),
        contraindications: Contraindications | None = None,
        clock: Clock,
    ) -> Exercise:
        """Creates a brand-new Exercise in the Active state and records
        `ExerciseCreated`. `exercise_id` is generated by the caller
        (`ExerciseId.generate()`) before calling this — the same
        convention `User.register()` and `Workout.plan()` follow.
        """
        created_at = clock.now()
        exercise = cls(
            exercise_id,
            name=name,
            movement_pattern=movement_pattern,
            difficulty=difficulty,
            instructions=instructions,
            created_at=created_at,
            description=description,
            primary_muscles=primary_muscles,
            secondary_muscles=secondary_muscles,
            equipment_requirements=equipment_requirements,
            contraindications=contraindications,
        )
        exercise.record_event(
            ExerciseCreated(
                occurred_at=created_at,
                exercise_id=exercise_id,
                name=name,
                movement_pattern=movement_pattern,
                difficulty=difficulty,
            )
        )
        return exercise

    @property
    def name(self) -> ExerciseName:
        return self._name

    @property
    def movement_pattern(self) -> MovementPattern:
        return self._movement_pattern

    @property
    def difficulty(self) -> Difficulty:
        return self._difficulty

    @property
    def instructions(self) -> ExerciseInstructions:
        return self._instructions

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def description(self) -> ExerciseDescription | None:
        return self._description

    @property
    def primary_muscles(self) -> tuple[PrimaryMuscle, ...]:
        return self._primary_muscles

    @property
    def secondary_muscles(self) -> SecondaryMuscles:
        return self._secondary_muscles

    @property
    def equipment_requirements(self) -> frozenset[EquipmentRequirement]:
        return self._equipment_requirements

    @property
    def contraindications(self) -> Contraindications:
        return self._contraindications

    @property
    def status(self) -> ExerciseStatus:
        return self._status

    @property
    def updated_at(self) -> datetime | None:
        return self._updated_at

    @property
    def deprecated_at(self) -> datetime | None:
        return self._deprecated_at

    def update(
        self,
        *,
        clock: Clock,
        name: ExerciseName | None = None,
        description: ExerciseDescription | None = None,
        movement_pattern: MovementPattern | None = None,
        difficulty: Difficulty | None = None,
        instructions: ExerciseInstructions | None = None,
        primary_muscles: tuple[PrimaryMuscle, ...] | None = None,
        secondary_muscles: SecondaryMuscles | None = None,
        equipment_requirements: frozenset[EquipmentRequirement] | None = None,
        contraindications: Contraindications | None = None,
    ) -> None:
        """Replaces whichever fields are given (`None` means "leave
        unchanged", not "clear it" — pass an empty value object explicitly
        to clear one), re-validates the cross-field muscle invariant
        against the resulting combination, and records one `ExerciseUpdated`
        event. Blocked once Deprecated: "Deprecated exercises cannot be
        modified."
        """
        self._ensure_mutable()
        next_primary_muscles = (
            primary_muscles if primary_muscles is not None else self._primary_muscles
        )
        next_secondary_muscles = (
            secondary_muscles if secondary_muscles is not None else self._secondary_muscles
        )
        _ensure_no_muscle_overlap(next_primary_muscles, next_secondary_muscles)

        if name is not None:
            self._name = name
        if description is not None:
            self._description = description
        if movement_pattern is not None:
            self._movement_pattern = movement_pattern
        if difficulty is not None:
            self._difficulty = difficulty
        if instructions is not None:
            self._instructions = instructions
        self._primary_muscles = next_primary_muscles
        self._secondary_muscles = next_secondary_muscles
        if equipment_requirements is not None:
            self._equipment_requirements = equipment_requirements
        if contraindications is not None:
            self._contraindications = contraindications

        self._updated_at = clock.now()
        self.record_event(
            ExerciseUpdated(
                occurred_at=self._updated_at,
                exercise_id=self.id,
                name=self._name,
            )
        )

    def deprecate(self, *, clock: Clock) -> None:
        """Active -> Deprecated."""
        self._transition_to(ExerciseStatus.DEPRECATED)
        self._deprecated_at = clock.now()
        self.record_event(ExerciseDeprecated(occurred_at=self._deprecated_at, exercise_id=self.id))

    def _ensure_mutable(self) -> None:
        ensure(
            self._status is not ExerciseStatus.DEPRECATED,
            f"cannot modify an exercise in status {self._status.value!r}",
        )

    def _transition_to(self, target: ExerciseStatus) -> None:
        allowed = _ALLOWED_TRANSITIONS[self._status]
        ensure(
            target in allowed,
            f"cannot transition exercise status from {self._status.value!r} to {target.value!r}",
        )
        self._status = target
