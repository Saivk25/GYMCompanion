"""Closed-set categorical values used by the Exercise aggregate.

`MovementPattern` and `Difficulty` cover both roles the task's own spec
named separately ("Suggested Value Objects: ... DifficultyLevel ...
MovementPattern" alongside "Enums: MovementPattern ... Difficulty"): each is
implemented once, as a plain `enum.Enum`, and used directly as the field
type on `Exercise` (`exercise.movement_pattern: MovementPattern`,
`exercise.difficulty: Difficulty`) — the same choice already made for
`AccountStatus` on `User` and `WorkoutStatus` on `Workout`. Wrapping either
in a second, otherwise-empty value object would add a layer of indirection
with no invariant left for it to enforce, which is exactly the kind of
speculative structure this project's engineering principles argue against.
"""

from enum import Enum


class MovementPattern(str, Enum):
    """The fundamental movement category an exercise belongs to — read by
    Substitution and Plan generation (not yet implemented) to find
    like-for-like alternatives. Domain Model & Decision Engine Bible,
    Section 4.5, Table 8 names `movement_pattern` as a key attribute of
    `Exercise` without enumerating its values; the nine listed here are
    this task's own specification.
    """

    PUSH = "push"
    PULL = "pull"
    HINGE = "hinge"
    SQUAT = "squat"
    LUNGE = "lunge"
    CARRY = "carry"
    ROTATION = "rotation"
    CORE = "core"
    CARDIO = "cardio"


class Difficulty(str, Enum):
    """How much training experience an exercise assumes. Read by Plan
    generation (not yet implemented) alongside `UserProfile.experience_level`
    (`app.domain.user.enums.ExperienceLevel`) — a deliberately separate enum
    from that one: a beginner-appropriate exercise and a beginner user are
    related concepts but not the same type, and merging them would make an
    exercise's difficulty accidentally depend on the User aggregate's shape.
    """

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class ExerciseStatus(str, Enum):
    """The Exercise aggregate's lifecycle: Active -> Deprecated, one
    directional and terminal. See
    `docs/adr/0007-exercise-aggregate-first-increment.md` for why this is
    two states rather than the Bible's four (Draft -> Reviewed ->
    Published -> Deprecated, Section 4.5, Table 8) — that curation pipeline
    belongs to the Knowledge Graph increment this task explicitly excludes.
    Legal transitions are enforced by `Exercise`'s own transition table
    (`exercise.py`), not by this enum.
    """

    ACTIVE = "active"
    DEPRECATED = "deprecated"
