"""Shared test helpers for the Training Load Rule Engine's test suite.

Not itself a test file (no `test_` prefix, so pytest never collects it) —
mirrors `tests/domain/safety/rules/factories.py`'s reasoning exactly.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date, timedelta

from app.domain.training_load.rules.context import (
    TrainingLoad,
    TrainingLoadDate,
    TrainingLoadRuleContext,
    TrainingLoadSummary,
)

_A_START_DATE = date(2026, 1, 1)


def a_training_load_summary(
    *, load_date: date = _A_START_DATE, load: float = 500.0
) -> TrainingLoadSummary:
    return TrainingLoadSummary(load_date=TrainingLoadDate(load_date), load=TrainingLoad(load))


def daily_summaries(
    loads: Sequence[float], *, start_date: date = _A_START_DATE
) -> list[TrainingLoadSummary]:
    """Builds one `TrainingLoadSummary` per day, starting at `start_date`
    and incrementing by one calendar day per entry — the common shape
    almost every test in this package needs."""
    return [
        a_training_load_summary(load_date=start_date + timedelta(days=i), load=load)
        for i, load in enumerate(loads)
    ]


def a_training_load_context(
    *, history: Sequence[TrainingLoadSummary] = ()
) -> TrainingLoadRuleContext:
    return TrainingLoadRuleContext(history=tuple(history))
