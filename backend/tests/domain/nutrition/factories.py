"""Shared test helpers for the Nutrition aggregate's test suite.

Not itself a test file (no `test_` prefix, so pytest never collects it) —
mirrors `tests/domain/progress/factories.py`'s reasoning exactly.
"""

from datetime import date, datetime, timezone

from app.domain.nutrition.identifiers import NutritionId
from app.domain.nutrition.nutrition import Nutrition
from app.domain.nutrition.value_objects import NutritionDate
from app.domain.shared_kernel.clock import FixedClock
from app.domain.user.identifiers import UserId

_A_FIXED_INSTANT = datetime(2026, 1, 1, tzinfo=timezone.utc)


def a_fixed_clock() -> FixedClock:
    """A `FixedClock` pinned to an arbitrary, fixed instant — deterministic
    and irrelevant to what any test in this package actually asserts about,
    beyond that `Clock.now()` was consulted rather than the system clock.
    """
    return FixedClock(_A_FIXED_INSTANT)


def a_recorded_nutrition(*, user_id: UserId | None = None) -> Nutrition:
    """A freshly recorded Nutrition entry with no optional fields set —
    the common starting point most tests in this package build on."""
    return Nutrition.record(
        nutrition_id=NutritionId.generate(),
        user_id=user_id or UserId.generate(),
        nutrition_date=NutritionDate(date(2026, 1, 1)),
        clock=a_fixed_clock(),
    )
