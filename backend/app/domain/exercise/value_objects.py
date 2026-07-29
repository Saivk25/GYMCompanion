"""Immutable value objects owned by the Exercise aggregate.

Every type here is a `ValueObject` subclass (`app.domain.shared_kernel`):
no identity, replaced wholesale on change, validated once at construction —
the same discipline `app.domain.user.value_objects` and
`app.domain.workout.value_objects` follow.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.domain.shared_kernel.validation import ensure, ensure_not_empty
from app.domain.shared_kernel.value_object import ValueObject

_MAX_EXERCISE_NAME_LENGTH = 200
_MAX_DESCRIPTION_LENGTH = 1000
_MAX_INSTRUCTIONS_LENGTH = 5000
_MAX_MUSCLE_NAME_LENGTH = 100
_MAX_EQUIPMENT_NAME_LENGTH = 100
_MAX_CONTRAINDICATION_TAG_LENGTH = 100


def _normalize(value: str, *, field_name: str) -> str:
    """Shared normalization for the free-text "name of a thing" fields
    below (muscles, equipment, contraindication tags): trimmed and
    lower-cased so equality/deduplication (`PrimaryMuscle`'s "no duplicate",
    `Exercise`'s "primary cannot also appear as secondary") compares
    meaning, not incidental casing — `PrimaryMuscle("Chest")` and
    `PrimaryMuscle("chest")` naming the same muscle twice under different
    casing would otherwise silently defeat both rules.
    """
    ensure_not_empty(value, field_name)
    return value.strip().lower()


@dataclass(frozen=True)
class ExerciseName(ValueObject):
    """The exercise's canonical name, e.g. `ExerciseName("Barbell Bench
    Press")`. Required on every `Exercise` — "Exercise name cannot be
    empty" is enforced right here, the same placement
    `app.domain.workout.value_objects.WorkoutName` uses.
    """

    value: str

    def __post_init__(self) -> None:
        ensure_not_empty(self.value, "exercise name")
        ensure(
            len(self.value) <= _MAX_EXERCISE_NAME_LENGTH,
            f"exercise name must be at most {_MAX_EXERCISE_NAME_LENGTH} characters, "
            f"got {len(self.value)}",
        )


@dataclass(frozen=True)
class ExerciseDescription(ValueObject):
    """A short, free-text description of the exercise. Optional on
    `Exercise` (`description: ExerciseDescription | None`); validated
    non-empty on the same principle as
    `app.domain.workout.value_objects.WorkoutNotes` — if there's nothing to
    say, the field should be `None`, not an `ExerciseDescription` holding
    an empty string.
    """

    value: str

    def __post_init__(self) -> None:
        ensure_not_empty(self.value, "exercise description")
        ensure(
            len(self.value) <= _MAX_DESCRIPTION_LENGTH,
            f"exercise description must be at most {_MAX_DESCRIPTION_LENGTH} characters, "
            f"got {len(self.value)}",
        )


@dataclass(frozen=True)
class ExerciseInstructions(ValueObject):
    """How to perform the exercise — required on every `Exercise`.
    "Instructions cannot be empty" is enforced right here.
    """

    value: str

    def __post_init__(self) -> None:
        ensure_not_empty(self.value, "exercise instructions")
        ensure(
            len(self.value) <= _MAX_INSTRUCTIONS_LENGTH,
            f"exercise instructions must be at most {_MAX_INSTRUCTIONS_LENGTH} characters, "
            f"got {len(self.value)}",
        )


@dataclass(frozen=True)
class EquipmentRequirement(ValueObject):
    """One piece of equipment this exercise needs, e.g.
    `EquipmentRequirement("barbell")`. Mirrors the Bible's `Equipment`
    value object shape (Section 5: "One piece of available equipment
    within an EnvironmentContext") but is a distinct type — that one
    describes what a *Context* has available; this one describes what an
    *Exercise* needs. `Exercise.equipment_requirements` holds a
    `frozenset[EquipmentRequirement]`; a plain bodyweight exercise has an
    empty set, not a special sentinel value.
    """

    value: str

    def __post_init__(self) -> None:
        normalized = _normalize(self.value, field_name="equipment requirement")
        ensure(
            len(normalized) <= _MAX_EQUIPMENT_NAME_LENGTH,
            f"equipment requirement must be at most {_MAX_EQUIPMENT_NAME_LENGTH} characters, "
            f"got {len(normalized)}",
        )
        object.__setattr__(self, "value", normalized)


@dataclass(frozen=True)
class PrimaryMuscle(ValueObject):
    """One muscle this exercise primarily trains, e.g.
    `PrimaryMuscle("chest")`. `Exercise.primary_muscles` holds a tuple of
    these — a compound movement like a bench press legitimately has more
    than one (chest, triceps, front delts), so this is a per-muscle value
    object, not a single field. Normalized (trimmed, lower-cased) at
    construction — see `_normalize`'s docstring for why: it's what makes
    "no duplicate primary muscle" and "primary muscle cannot also appear
    as secondary" (both enforced on `Exercise`, since only the aggregate
    can see both `primary_muscles` and `secondary_muscles` at once)
    actually meaningful checks rather than ones a casing difference could
    silently defeat.
    """

    value: str

    def __post_init__(self) -> None:
        normalized = _normalize(self.value, field_name="primary muscle")
        ensure(
            len(normalized) <= _MAX_MUSCLE_NAME_LENGTH,
            f"primary muscle must be at most {_MAX_MUSCLE_NAME_LENGTH} characters, "
            f"got {len(normalized)}",
        )
        object.__setattr__(self, "value", normalized)


@dataclass(frozen=True)
class SecondaryMuscles(ValueObject):
    """The set of muscles this exercise secondarily trains. A collection
    value object, not a tuple of per-muscle value objects like
    `PrimaryMuscle` — the task names a rule for *duplicate primary*
    muscles specifically, not secondary ones, so this stores a
    `frozenset[str]` (structurally duplicate-free by construction) rather
    than raising on a duplicate the way `Exercise`'s primary-muscle check
    does. Every entry is still normalized and validated non-empty, the
    same as `PrimaryMuscle`.
    """

    values: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        normalized = frozenset(
            _normalize(value, field_name="secondary muscle") for value in self.values
        )
        for value in normalized:
            ensure(
                len(value) <= _MAX_MUSCLE_NAME_LENGTH,
                f"secondary muscle must be at most {_MAX_MUSCLE_NAME_LENGTH} characters, "
                f"got {len(value)}",
            )
        object.__setattr__(self, "values", normalized)


@dataclass(frozen=True)
class Contraindications(ValueObject):
    """The set of contraindication tags this exercise is flagged with —
    Domain Model & Decision Engine Bible, Section 4.5, Table 8's
    `contraindication_tags`, checked against a user's active `SafetyFlag`s
    (not yet modeled) before an exercise may appear in any Plan or
    Substitution result. Defaults to empty — the Bible allows a
    contraindication list to be empty, only requiring that it be
    *reviewed*; the review workflow itself belongs to the Knowledge Graph
    increment (see the ADR), so every `Exercise` here is a
    single always-current tag set with no separate reviewed/unreviewed
    state.
    """

    tags: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        normalized = frozenset(
            _normalize(tag, field_name="contraindication tag") for tag in self.tags
        )
        for tag in normalized:
            ensure(
                len(tag) <= _MAX_CONTRAINDICATION_TAG_LENGTH,
                f"contraindication tag must be at most {_MAX_CONTRAINDICATION_TAG_LENGTH} "
                f"characters, got {len(tag)}",
            )
        object.__setattr__(self, "tags", normalized)
