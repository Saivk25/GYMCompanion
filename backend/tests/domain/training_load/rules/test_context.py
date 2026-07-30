"""Tests for app/domain/training_load/rules/context.py."""

from datetime import date

import pytest

from app.domain.rules.context import RuleContext
from app.domain.shared_kernel.errors import DomainInvariantViolationError
from app.domain.training_load.rules.context import (
    TrainingLoad,
    TrainingLoadRuleContext,
)
from tests.domain.training_load.rules.factories import a_training_load_summary, daily_summaries

# --- TrainingLoad ---


@pytest.mark.unit
def test_training_load_allows_zero() -> None:
    assert TrainingLoad(0.0).value == 0.0


@pytest.mark.unit
def test_training_load_rejects_negative() -> None:
    with pytest.raises(DomainInvariantViolationError):
        TrainingLoad(-1.0)


# --- TrainingLoadRuleContext basics ---


@pytest.mark.unit
def test_is_a_rule_context() -> None:
    assert isinstance(TrainingLoadRuleContext(history=()), RuleContext)


@pytest.mark.unit
def test_is_immutable() -> None:
    context = TrainingLoadRuleContext(history=())
    with pytest.raises(AttributeError):
        context.history = (a_training_load_summary(),)  # type: ignore[misc]


# --- from_summaries() ---


@pytest.mark.unit
def test_from_summaries_sorts_chronologically() -> None:
    later = a_training_load_summary(load_date=date(2026, 1, 10), load=100.0)
    earlier = a_training_load_summary(load_date=date(2026, 1, 1), load=200.0)
    context = TrainingLoadRuleContext.from_summaries([later, earlier])
    assert context.history == (earlier, later)


@pytest.mark.unit
def test_from_summaries_with_no_entries_is_empty() -> None:
    assert TrainingLoadRuleContext.from_summaries([]).history == ()


@pytest.mark.unit
def test_from_summaries_does_not_reflect_a_later_mutated_list() -> None:
    source = [a_training_load_summary(load_date=date(2026, 1, 1))]
    context = TrainingLoadRuleContext.from_summaries(source)
    source.append(a_training_load_summary(load_date=date(2026, 1, 2)))
    assert len(context.history) == 1


# --- trailing_window() ---


@pytest.mark.unit
def test_trailing_window_with_empty_history_is_empty() -> None:
    context = TrainingLoadRuleContext(history=())
    assert context.trailing_window(window_days=7) == ()


@pytest.mark.unit
def test_trailing_window_includes_only_entries_within_range() -> None:
    summaries = daily_summaries([100.0] * 10, start_date=date(2026, 1, 1))
    context = TrainingLoadRuleContext.from_summaries(summaries)
    window = context.trailing_window(window_days=7)
    # Latest entry is 2026-01-10; a 7-day window includes 01-04..01-10 inclusive.
    assert len(window) == 7
    assert window[0].load_date.value == date(2026, 1, 4)
    assert window[-1].load_date.value == date(2026, 1, 10)


@pytest.mark.unit
def test_trailing_window_with_gaps_only_returns_entries_that_exist() -> None:
    sparse = [
        a_training_load_summary(load_date=date(2026, 1, 1), load=100.0),
        a_training_load_summary(load_date=date(2026, 1, 20), load=200.0),
    ]
    context = TrainingLoadRuleContext.from_summaries(sparse)
    window = context.trailing_window(window_days=7)
    assert len(window) == 1
    assert window[0].load_date.value == date(2026, 1, 20)


@pytest.mark.unit
def test_trailing_window_is_anchored_to_latest_entry_not_today() -> None:
    """No wall-clock reads — the window is always anchored to the latest
    supplied entry, however far in the past or future that is."""
    summaries = daily_summaries([100.0] * 3, start_date=date(2020, 1, 1))
    context = TrainingLoadRuleContext.from_summaries(summaries)
    window = context.trailing_window(window_days=7)
    assert len(window) == 3


# --- determinism ---


@pytest.mark.unit
def test_trailing_window_is_deterministic() -> None:
    summaries = daily_summaries([100.0] * 10)
    context = TrainingLoadRuleContext.from_summaries(summaries)
    assert context.trailing_window(window_days=7) == context.trailing_window(window_days=7)
