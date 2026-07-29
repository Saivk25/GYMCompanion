"""Shared test helpers for the Workout aggregate's test suite.

Not itself a test file (no `test_` prefix, so pytest never collects it) —
mirrors `tests/domain/user/factories.py`'s reasoning exactly.
"""

from datetime import date, datetime, timezone

from app.domain.shared_kernel.clock import FixedClock
from app.domain.user.identifiers import UserId
from app.domain.workout.identifiers import WorkoutId
from app.domain.workout.value_objects import WorkoutDate, WorkoutName
from app.domain.workout.workout import Workout

_A_FIXED_INSTANT = datetime(2026, 1, 1, tzinfo=timezone.utc)


def a_fixed_clock() -> FixedClock:
    """A `FixedClock` pinned to an arbitrary, fixed instant — deterministic
    and irrelevant to what any test in this package actually asserts about,
    beyond that `Clock.now()` was consulted rather than the system clock.
    """
    return FixedClock(_A_FIXED_INSTANT)


def a_planned_workout(*, user_id: UserId | None = None) -> Workout:
    """A freshly planned Workout — the common starting point most tests in
    this package build on."""
    return Workout.plan(
        workout_id=WorkoutId.generate(),
        user_id=user_id or UserId.generate(),
        name=WorkoutName("Push Day"),
        planned_date=WorkoutDate(date(2026, 1, 1)),
        clock=a_fixed_clock(),
    )
