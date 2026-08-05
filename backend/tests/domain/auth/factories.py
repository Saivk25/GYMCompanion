"""Shared test helpers for the Credential aggregate's test suite. Not
itself a test file (no `test_` prefix, so pytest never collects it).
"""

from datetime import datetime, timezone

from app.domain.shared_kernel.clock import FixedClock

_A_FIXED_INSTANT = datetime(2026, 1, 1, tzinfo=timezone.utc)


def a_fixed_clock() -> FixedClock:
    """A `FixedClock` pinned to an arbitrary, fixed instant — same
    reasoning as `tests.domain.user.factories.a_fixed_clock`."""
    return FixedClock(_A_FIXED_INSTANT)
