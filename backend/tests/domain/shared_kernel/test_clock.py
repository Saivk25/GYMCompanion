"""Tests for app/domain/shared_kernel/clock.py.

This is the concrete proof of the "Time abstraction is testable"
requirement: every assertion here is about time-dependent behavior, and
none of them sleep, retry, or tolerate a millisecond of slack — because
FixedClock makes "now" a value under the test's control, not the system
clock's.
"""

from datetime import datetime, timedelta, timezone

import pytest

from app.domain.shared_kernel.clock import Clock, FixedClock, SystemClock


@pytest.mark.unit
def test_system_clock_returns_a_timezone_aware_utc_datetime() -> None:
    result = SystemClock().now()
    assert result.tzinfo is not None
    assert result.utcoffset() == timedelta(0)


@pytest.mark.unit
def test_system_clock_is_a_clock() -> None:
    assert isinstance(SystemClock(), Clock)


@pytest.mark.unit
def test_fixed_clock_returns_exactly_the_configured_time() -> None:
    fixed = datetime(2026, 1, 1, tzinfo=timezone.utc)
    clock = FixedClock(fixed)
    assert clock.now() == fixed
    assert clock.now() == fixed  # calling twice must not drift, unlike a real clock


@pytest.mark.unit
def test_fixed_clock_rejects_a_naive_datetime() -> None:
    naive = datetime(2026, 1, 1)  # deliberately naive - the whole point of this test
    with pytest.raises(ValueError, match="timezone-aware"):
        FixedClock(naive)


@pytest.mark.unit
def test_fixed_clock_advance_moves_time_forward_deterministically() -> None:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    clock = FixedClock(start)

    clock.advance(timedelta(days=1))

    assert clock.now() == datetime(2026, 1, 2, tzinfo=timezone.utc)


@pytest.mark.unit
def test_clock_cannot_be_instantiated_directly() -> None:
    """Clock is the abstraction domain code depends on; only SystemClock
    and FixedClock (or a future test double) should ever be constructed."""
    with pytest.raises(TypeError):
        Clock()  # type: ignore[abstract]
