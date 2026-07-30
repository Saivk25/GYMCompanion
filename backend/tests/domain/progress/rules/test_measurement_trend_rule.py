"""Tests for app/domain/progress/rules/measurement_trend_rule.py."""

from datetime import date

import pytest

from app.domain.progress.rules.measurement_trend_rule import MeasurementTrendRule
from app.domain.progress.value_objects import (
    ChestMeasurement,
    MuscleMass,
    ProgressDate,
    WaistMeasurement,
)
from app.domain.rules.result import RuleId
from app.domain.rules.severity import RecommendationSeverity
from tests.domain.progress.rules.factories import a_progress_context, a_progress_evaluation_context

# --- identity ---


@pytest.mark.unit
def test_default_identity() -> None:
    rule = MeasurementTrendRule()
    assert rule.id == RuleId("progress_evaluation.measurement_trend")
    assert rule.name == "Measurement Trend"
    assert rule.severity == RecommendationSeverity.ADVISORY


# --- never fails ---


@pytest.mark.unit
def test_passes_with_no_history() -> None:
    rule = MeasurementTrendRule()
    result = rule.evaluate(a_progress_evaluation_context())
    assert result.passed is True
    assert result.triggered_rules == ()


@pytest.mark.unit
def test_passes_when_no_field_has_enough_entries() -> None:
    rule = MeasurementTrendRule(minimum_entries=2)
    context = a_progress_evaluation_context(
        progress_history=[a_progress_context(waist=WaistMeasurement(80.0))]
    )
    result = rule.evaluate(context)
    assert result.passed is True
    assert "No measurement field" in result.explanation


@pytest.mark.unit
def test_passes_with_no_trend_beyond_noise_threshold() -> None:
    rule = MeasurementTrendRule(minimum_entries=2, minimum_change=1.0)
    context = a_progress_evaluation_context(
        progress_history=[
            a_progress_context(
                progress_date=ProgressDate(date(2026, 1, 1)), waist=WaistMeasurement(80.0)
            ),
            a_progress_context(
                progress_date=ProgressDate(date(2026, 1, 15)), waist=WaistMeasurement(80.3)
            ),
        ]
    )
    result = rule.evaluate(context)
    assert result.passed is True
    assert "No measurement changed" in result.explanation


# --- trend detection ---


@pytest.mark.unit
def test_reports_a_decreasing_trend() -> None:
    rule = MeasurementTrendRule(minimum_entries=2, minimum_change=1.0)
    context = a_progress_evaluation_context(
        progress_history=[
            a_progress_context(
                progress_date=ProgressDate(date(2026, 1, 1)), waist=WaistMeasurement(85.0)
            ),
            a_progress_context(
                progress_date=ProgressDate(date(2026, 1, 15)), waist=WaistMeasurement(80.0)
            ),
        ]
    )
    result = rule.evaluate(context)
    assert result.passed is True
    assert "waist decreased by 5.0" in result.explanation
    assert len(result.recommendations) == 1


@pytest.mark.unit
def test_reports_an_increasing_trend() -> None:
    rule = MeasurementTrendRule(minimum_entries=2, minimum_change=1.0)
    context = a_progress_evaluation_context(
        progress_history=[
            a_progress_context(
                progress_date=ProgressDate(date(2026, 1, 1)), chest=ChestMeasurement(95.0)
            ),
            a_progress_context(
                progress_date=ProgressDate(date(2026, 1, 15)), chest=ChestMeasurement(98.0)
            ),
        ]
    )
    result = rule.evaluate(context)
    assert result.passed is True
    assert "chest increased by 3.0" in result.explanation


@pytest.mark.unit
def test_reports_multiple_trending_fields() -> None:
    rule = MeasurementTrendRule(minimum_entries=2, minimum_change=1.0)
    context = a_progress_evaluation_context(
        progress_history=[
            a_progress_context(
                progress_date=ProgressDate(date(2026, 1, 1)),
                waist=WaistMeasurement(85.0),
                muscle_mass=MuscleMass(30.0),
            ),
            a_progress_context(
                progress_date=ProgressDate(date(2026, 1, 15)),
                waist=WaistMeasurement(80.0),
                muscle_mass=MuscleMass(32.0),
            ),
        ]
    )
    result = rule.evaluate(context)
    assert "waist decreased by 5.0" in result.explanation
    assert "muscle mass increased by 2.0" in result.explanation


@pytest.mark.unit
def test_never_fails_even_with_a_large_change() -> None:
    """MeasurementTrendRule has no target to fail against — see its own
    module docstring for the StrengthGoalRule-precedent reasoning."""
    rule = MeasurementTrendRule(minimum_entries=2, minimum_change=1.0)
    context = a_progress_evaluation_context(
        progress_history=[
            a_progress_context(
                progress_date=ProgressDate(date(2026, 1, 1)), waist=WaistMeasurement(100.0)
            ),
            a_progress_context(
                progress_date=ProgressDate(date(2026, 1, 15)), waist=WaistMeasurement(70.0)
            ),
        ]
    )
    result = rule.evaluate(context)
    assert result.passed is True
    assert result.triggered_rules == ()


# --- determinism ---


@pytest.mark.unit
def test_evaluate_is_deterministic() -> None:
    rule = MeasurementTrendRule()
    context = a_progress_evaluation_context(
        progress_history=[
            a_progress_context(
                progress_date=ProgressDate(date(2026, 1, 1)), waist=WaistMeasurement(85.0)
            ),
            a_progress_context(
                progress_date=ProgressDate(date(2026, 1, 15)), waist=WaistMeasurement(80.0)
            ),
        ]
    )
    assert rule.evaluate(context) == rule.evaluate(context)
