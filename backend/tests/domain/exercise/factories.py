"""Shared test helpers for the Exercise aggregate's test suite.

Not itself a test file (no `test_` prefix, so pytest never collects it) —
mirrors `tests/domain/user/factories.py` and
`tests/domain/workout/factories.py`'s reasoning exactly.
"""

from datetime import datetime, timezone

from app.domain.exercise.enums import Difficulty, MovementPattern
from app.domain.exercise.exercise import Exercise
from app.domain.exercise.identifiers import ExerciseId
from app.domain.exercise.value_objects import ExerciseInstructions, ExerciseName
from app.domain.shared_kernel.clock import FixedClock

_A_FIXED_INSTANT = datetime(2026, 1, 1, tzinfo=timezone.utc)


def a_fixed_clock() -> FixedClock:
    """A `FixedClock` pinned to an arbitrary, fixed instant — deterministic
    and irrelevant to what any test in this package actually asserts about,
    beyond that `Clock.now()` was consulted rather than the system clock.
    """
    return FixedClock(_A_FIXED_INSTANT)


def a_created_exercise() -> Exercise:
    """A freshly created, Active Exercise — the common starting point most
    tests in this package build on."""
    return Exercise.create(
        exercise_id=ExerciseId.generate(),
        name=ExerciseName("Barbell Bench Press"),
        movement_pattern=MovementPattern.PUSH,
        difficulty=Difficulty.INTERMEDIATE,
        instructions=ExerciseInstructions(
            "Lie on the bench, lower the bar to the chest, press up."
        ),
        clock=a_fixed_clock(),
    )
