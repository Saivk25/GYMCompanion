"""Shared test helpers for the Progress aggregate's test suite.

Not itself a test file (no `test_` prefix, so pytest never collects it) —
mirrors `tests/domain/workout_session/factories.py`'s reasoning exactly.
"""

from datetime import date, datetime, timezone

from app.domain.progress.enums import MeasurementUnit, ProgressSource
from app.domain.progress.identifiers import ProgressId
from app.domain.progress.progress import Progress
from app.domain.progress.value_objects import ProgressDate
from app.domain.shared_kernel.clock import FixedClock
from app.domain.user.identifiers import UserId

_A_FIXED_INSTANT = datetime(2026, 1, 1, tzinfo=timezone.utc)


def a_fixed_clock() -> FixedClock:
    """A `FixedClock` pinned to an arbitrary, fixed instant — deterministic
    and irrelevant to what any test in this package actually asserts about,
    beyond that `Clock.now()` was consulted rather than the system clock.
    """
    return FixedClock(_A_FIXED_INSTANT)


def a_recorded_progress(
    *,
    user_id: UserId | None = None,
    unit: MeasurementUnit = MeasurementUnit.METRIC,
    source: ProgressSource = ProgressSource.MANUAL,
) -> Progress:
    """A freshly recorded Progress check-in with no optional fields set —
    the common starting point most tests in this package build on."""
    return Progress.record(
        progress_id=ProgressId.generate(),
        user_id=user_id or UserId.generate(),
        progress_date=ProgressDate(date(2026, 1, 1)),
        unit=unit,
        source=source,
        clock=a_fixed_clock(),
    )
