"""Tests for app/domain/progress/rules/plateau_rule.py."""

from datetime import date, timedelta

import pytest

from app.domain.progress.context import ProgressContext
from app.domain.progress.rules.plateau_rule import PlateauRule
from app.domain.progress.value_objects import BodyFatPercentage, BodyWeight, ProgressDate
from app.domain.rules.result import RuleId
from app.domain.rules.severity import RecommendationSeverity
from tests.domain.progress.rules.factories import a_progress_context, a_progress_evaluation_context


def _weight_entries(weights: list[float]) -> list[ProgressContext]:
    start = date(2026, 1, 1)
    return [
        a_progress_context(
            progress_date=ProgressDate(start + timedelta(days=7 * i)), body_weight=BodyWeight(w)
        )
        for i, w in enumerate(weights)
    ]


def _body_fat_entries(percentages: list[float]) -> list[ProgressContext]:
    start = date(2026, 1, 1)
    return [
        a_progress_context(
            progress_date=ProgressDate(start + timedelta(days=7 * i)),
            body_fat_percentage=BodyFatPercentage(p),
        )
        for i, p in enumerate(percentages)
    ]


# --- identity ---


@pytest.mark.unit
def test_default_identity() -> None:
    rule = PlateauRule()
    assert rule.id == RuleId("progress_evaluation.plateau")
    assert rule.name == "Plateau"
    assert rule.severity == RecommendationSeverity.ADVISORY


# --- insufficient data ---


@pytest.mark.unit
def test_passes_when_neither_metric_has_enough_entries() -> None:
    rule = PlateauRule(minimum_consecutive_entries=4)
    context = a_progress_evaluation_context(progress_history=_weight_entries([80.0, 80.0]))
    result = rule.evaluate(context)
    assert result.passed is True
    assert "cannot assess a plateau" in result.explanation


# --- body weight plateau ---


@pytest.mark.unit
def test_fails_when_body_weight_is_flat() -> None:
    rule = PlateauRule(minimum_consecutive_entries=4, weight_plateau_tolerance=1.0)
    context = a_progress_evaluation_context(
        progress_history=_weight_entries([80.0, 80.4, 79.7, 80.2])
    )
    result = rule.evaluate(context)
    assert result.passed is False
    assert result.triggered_rules == (RuleId("progress_evaluation.plateau"),)
    assert "body weight" in result.explanation.lower()
    assert len(result.recommendations) == 1


@pytest.mark.unit
def test_passes_when_body_weight_moves_meaningfully() -> None:
    rule = PlateauRule(minimum_consecutive_entries=4, weight_plateau_tolerance=1.0)
    context = a_progress_evaluation_context(
        progress_history=_weight_entries([85.0, 83.0, 81.5, 80.0])
    )
    result = rule.evaluate(context)
    assert result.passed is True


@pytest.mark.unit
def test_only_considers_the_trailing_window() -> None:
    rule = PlateauRule(minimum_consecutive_entries=3, weight_plateau_tolerance=1.0)
    # First two entries show a big drop, but the trailing 3 are flat.
    context = a_progress_evaluation_context(
        progress_history=_weight_entries([95.0, 85.0, 80.0, 80.2, 79.8])
    )
    result = rule.evaluate(context)
    assert result.passed is False


# --- fallback to body fat percentage ---


@pytest.mark.unit
def test_falls_back_to_body_fat_when_weight_data_is_insufficient() -> None:
    rule = PlateauRule(minimum_consecutive_entries=4, body_fat_plateau_tolerance=1.0)
    context = a_progress_evaluation_context(
        progress_history=_body_fat_entries([20.0, 20.3, 19.7, 20.1])
    )
    result = rule.evaluate(context)
    assert result.passed is False
    assert "body fat percentage" in result.explanation.lower()


# --- determinism ---


@pytest.mark.unit
def test_evaluate_is_deterministic() -> None:
    rule = PlateauRule(minimum_consecutive_entries=4)
    context = a_progress_evaluation_context(
        progress_history=_weight_entries([80.0, 80.4, 79.7, 80.2])
    )
    assert rule.evaluate(context) == rule.evaluate(context)
