"""Shared test helpers for the Readiness aggregate's test suite.

Not itself a test file (no `test_` prefix, so pytest never collects it) —
mirrors `tests/domain/progress/factories.py`'s reasoning exactly.
"""

from datetime import date, datetime, timezone

from app.domain.readiness.identifiers import ReadinessId
from app.domain.readiness.readiness import Readiness
from app.domain.readiness.value_objects import ReadinessDate
from app.domain.shared_kernel.clock import FixedClock
from app.domain.user.identifiers import UserId

_A_FIXED_INSTANT = datetime(2026, 1, 1, tzinfo=timezone.utc)


def a_fixed_clock() -> FixedClock:
    """A `FixedClock` pinned to an arbitrary, fixed instant — deterministic
    and irrelevant to what any test in this package actually asserts about,
    beyond that `Clock.now()` was consulted rather than the system clock.
    """
    return FixedClock(_A_FIXED_INSTANT)


def a_recorded_readiness(*, user_id: UserId | None = None) -> Readiness:
    """A freshly recorded Readiness check-in with no optional fields set —
    the common starting point most tests in this package build on."""
    return Readiness.record(
        readiness_id=ReadinessId.generate(),
        user_id=user_id or UserId.generate(),
        readiness_date=ReadinessDate(date(2026, 1, 1)),
        clock=a_fixed_clock(),
    )
