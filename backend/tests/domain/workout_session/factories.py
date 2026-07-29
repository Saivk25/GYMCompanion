"""Shared test helpers for the WorkoutSession aggregate's test suite.

Not itself a test file (no `test_` prefix, so pytest never collects it) —
mirrors `tests/domain/user/factories.py`, `tests/domain/workout/
factories.py`, and `tests/domain/exercise/factories.py`'s reasoning
exactly.
"""

from datetime import date, datetime, timezone

from app.domain.shared_kernel.clock import FixedClock
from app.domain.user.identifiers import UserId
from app.domain.workout.identifiers import WorkoutId
from app.domain.workout_session.identifiers import WorkoutSessionId
from app.domain.workout_session.value_objects import SessionDate
from app.domain.workout_session.workout_session import WorkoutSession

_A_FIXED_INSTANT = datetime(2026, 1, 1, tzinfo=timezone.utc)


def a_fixed_clock() -> FixedClock:
    """A `FixedClock` pinned to an arbitrary, fixed instant — deterministic
    and irrelevant to what any test in this package actually asserts about,
    beyond that `Clock.now()` was consulted rather than the system clock.
    """
    return FixedClock(_A_FIXED_INSTANT)


def a_planned_session(
    *, workout_id: WorkoutId | None = None, user_id: UserId | None = None
) -> WorkoutSession:
    """A freshly planned WorkoutSession — the common starting point most
    tests in this package build on."""
    return WorkoutSession.plan(
        session_id=WorkoutSessionId.generate(),
        workout_id=workout_id or WorkoutId.generate(),
        user_id=user_id or UserId.generate(),
        session_date=SessionDate(date(2026, 1, 1)),
        clock=a_fixed_clock(),
    )
