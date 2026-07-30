"""Tests for app/domain/progress/rules/consistency_rule.py."""

from datetime import date

import pytest

from app.domain.progress.rules.consistency_rule import ConsistencyRule
from app.domain.progress.value_objects import ProgressDate
from app.domain.rules.result import RuleId
from app.domain.rules.severity import RecommendationSeverity
from tests.domain.progress.rules.factories import a_progress_context, a_progress_evaluation_context

# --- identity ---


@pytest.mark.unit
def test_default_identity() -> None:
    rule = ConsistencyRule()
    assert rule.id == RuleId("progress_evaluation.consistency")
    assert rule.name == "Consistency"
    assert rule.severity == RecommendationSeverity.ADVISORY


# --- insufficient entries: this rule deliberately fails, not passes ---


@pytest.mark.unit
def test_fails_with_no_entries_at_all() -> None:
    rule = ConsistencyRule(minimum_entries=3)
    context = a_progress_evaluation_context(progress_history=[], reference_date=date(2026, 1, 1))
    result = rule.evaluate(context)
    assert result.passed is False
    assert result.triggered_rules == (RuleId("progress_evaluation.consistency"),)
    assert len(result.recommendations) == 1


@pytest.mark.unit
def test_fails_below_minimum_entries() -> None:
    rule = ConsistencyRule(minimum_entries=3)
    context = a_progress_evaluation_context(
        progress_history=[
            a_progress_context(progress_date=ProgressDate(date(2026, 1, 1))),
            a_progress_context(progress_date=ProgressDate(date(2026, 1, 8))),
        ],
        reference_date=date(2026, 1, 8),
    )
    result = rule.evaluate(context)
    assert result.passed is False
    assert "at least 3" in result.explanation


# --- staleness ---


@pytest.mark.unit
def test_fails_when_most_recent_entry_is_stale() -> None:
    rule = ConsistencyRule(minimum_entries=2, maximum_days_since_last_entry=14)
    context = a_progress_evaluation_context(
        progress_history=[
            a_progress_context(progress_date=ProgressDate(date(2026, 1, 1))),
            a_progress_context(progress_date=ProgressDate(date(2026, 1, 5))),
        ],
        reference_date=date(2026, 2, 1),
    )
    result = rule.evaluate(context)
    assert result.passed is False
    assert "beyond the 14-day freshness window" in result.explanation


@pytest.mark.unit
def test_passes_with_enough_recent_entries() -> None:
    rule = ConsistencyRule(minimum_entries=2, maximum_days_since_last_entry=14)
    context = a_progress_evaluation_context(
        progress_history=[
            a_progress_context(progress_date=ProgressDate(date(2026, 1, 1))),
            a_progress_context(progress_date=ProgressDate(date(2026, 1, 20))),
        ],
        reference_date=date(2026, 1, 25),
    )
    result = rule.evaluate(context)
    assert result.passed is True
    assert "sufficient for meaningful evaluation" in result.explanation


# --- determinism ---


@pytest.mark.unit
def test_evaluate_is_deterministic() -> None:
    rule = ConsistencyRule()
    context = a_progress_evaluation_context(
        progress_history=[a_progress_context()], reference_date=date(2026, 1, 1)
    )
    assert rule.evaluate(context) == rule.evaluate(context)
