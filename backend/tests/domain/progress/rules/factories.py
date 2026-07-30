"""Shared test helpers for the Progress Evaluation Rule Engine's test
suite.

Not itself a test file (no `test_` prefix, so pytest never collects it).
Reuses `a_goal_context()`/`a_progress_context()` from
`tests.domain.goal.rules.factories` directly rather than duplicating
them — both build the exact snapshot types this package's context also
needs, with every field this package's rules read already overridable.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date, datetime, timezone

from app.domain.goal.context import GoalContext
from app.domain.progress.context import ProgressContext
from app.domain.progress.rules.context import ProgressEvaluationRuleContext
from app.domain.shared_kernel.clock import FixedClock
from tests.domain.goal.rules.factories import a_goal_context, a_progress_context

__all__ = ["a_fixed_clock", "a_goal_context", "a_progress_context", "a_progress_evaluation_context"]

_A_FIXED_INSTANT = datetime(2026, 1, 1, tzinfo=timezone.utc)
_A_REFERENCE_DATE = date(2026, 1, 1)


def a_fixed_clock() -> FixedClock:
    """A `FixedClock` pinned to an arbitrary, fixed instant — deterministic
    and irrelevant to what any test in this package actually asserts about,
    beyond that `Clock.now()` was consulted rather than the system clock.
    """
    return FixedClock(_A_FIXED_INSTANT)


def a_progress_evaluation_context(
    *,
    progress_history: Sequence[ProgressContext] = (),
    goal: GoalContext | None = None,
    reference_date: date = _A_REFERENCE_DATE,
) -> ProgressEvaluationRuleContext:
    """A `ProgressEvaluationRuleContext` wrapping the given fields as-is
    (no sorting/filtering — direct construction, see that class's own
    docstring); the common starting point most tests in this package
    build on."""
    return ProgressEvaluationRuleContext(
        progress_history=tuple(progress_history),
        goal=goal,
        reference_date=reference_date,
    )
