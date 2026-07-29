"""Shared test helpers for the Goal aggregate's test suite.

Not itself a test file (no `test_` prefix, so pytest never collects it) —
mirrors `tests/domain/readiness/factories.py`'s reasoning exactly.
"""

from datetime import date, datetime, timezone

from app.domain.goal.enums import GoalType
from app.domain.goal.goal import Goal
from app.domain.goal.identifiers import GoalId
from app.domain.goal.value_objects import GoalName, TargetDate
from app.domain.shared_kernel.clock import FixedClock
from app.domain.user.identifiers import UserId

_A_FIXED_INSTANT = datetime(2026, 1, 1, tzinfo=timezone.utc)


def a_fixed_clock() -> FixedClock:
    """A `FixedClock` pinned to an arbitrary, fixed instant — deterministic
    and irrelevant to what any test in this package actually asserts about,
    beyond that `Clock.now()` was consulted rather than the system clock.
    """
    return FixedClock(_A_FIXED_INSTANT)


def a_created_goal(*, user_id: UserId | None = None) -> Goal:
    """A freshly created, Active Goal with no optional fields set — the
    common starting point most tests in this package build on."""
    return Goal.create(
        goal_id=GoalId.generate(),
        user_id=user_id or UserId.generate(),
        goal_type=GoalType.LOSE_FAT,
        name=GoalName("Lose 5kg"),
        target_date=TargetDate(date(2026, 6, 1)),
        clock=a_fixed_clock(),
    )
