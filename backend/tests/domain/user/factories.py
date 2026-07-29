"""Shared test helpers for the User aggregate's test suite.

Not itself a test file (no `test_` prefix, so pytest never collects it) —
just the one `FixedClock` construction every other file in this package
would otherwise repeat verbatim.
"""

from datetime import datetime, timezone

from app.domain.shared_kernel.clock import FixedClock

_A_FIXED_INSTANT = datetime(2026, 1, 1, tzinfo=timezone.utc)


def a_fixed_clock() -> FixedClock:
    """A `FixedClock` pinned to an arbitrary, fixed instant — deterministic
    and irrelevant to what any test in this package actually asserts about,
    beyond that `Clock.now()` was consulted rather than the system clock.
    """
    return FixedClock(_A_FIXED_INSTANT)
