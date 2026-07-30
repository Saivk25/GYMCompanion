"""Tests for app/domain/progress/rules/progress_evaluation_rule_engine.py."""

from datetime import date, timedelta

import pytest

from app.domain.goal.value_objects import TargetWeight
from app.domain.progress.rules.body_fat_rule import BodyFatRule
from app.domain.progress.rules.body_weight_rule import BodyWeightRule
from app.domain.progress.rules.consistency_rule import ConsistencyRule
from app.domain.progress.rules.measurement_trend_rule import MeasurementTrendRule
from app.domain.progress.rules.plateau_rule import PlateauRule
from app.domain.progress.rules.progress_evaluation_rule_engine import ProgressEvaluationRuleEngine
from app.domain.progress.value_objects import BodyWeight, ProgressDate
from app.domain.rules.engine import RuleEngine
from app.domain.rules.result import RuleId
from tests.domain.progress.rules.factories import (
    a_goal_context,
    a_progress_context,
    a_progress_evaluation_context,
)


@pytest.mark.unit
def test_is_a_rule_engine() -> None:
    assert isinstance(ProgressEvaluationRuleEngine(), RuleEngine)


@pytest.mark.unit
def test_default_construction_registers_all_five_rules() -> None:
    engine = ProgressEvaluationRuleEngine()
    rule_types = {type(rule) for rule in engine.rules}
    expected_rule_types: set[type[object]] = {
        BodyWeightRule,
        BodyFatRule,
        MeasurementTrendRule,
        ConsistencyRule,
        PlateauRule,
    }
    assert rule_types == expected_rule_types
    assert len(engine.rules) == 5


@pytest.mark.unit
def test_accepts_a_custom_rule_set() -> None:
    custom_rule = BodyWeightRule(rule_id=RuleId("custom.body_weight"))
    engine = ProgressEvaluationRuleEngine([custom_rule])
    assert engine.rules == (custom_rule,)


# --- evaluate(): a context with enough data and no red flags ---


@pytest.mark.unit
def test_evaluating_an_empty_context_fails_on_consistency_only() -> None:
    """With no progress history at all, only ConsistencyRule (which
    deliberately fails on insufficient data) should trigger."""
    result = ProgressEvaluationRuleEngine().evaluate(a_progress_evaluation_context())
    assert result.passed is False
    assert result.triggered_rules == (RuleId("progress_evaluation.consistency"),)


@pytest.mark.unit
def test_evaluating_a_healthy_history_passes() -> None:
    start = date(2026, 1, 1)
    history = [
        a_progress_context(
            progress_date=ProgressDate(start + timedelta(days=7 * i)),
            body_weight=BodyWeight(90.0 - i * 3.0),
        )
        for i in range(4)
    ]
    goal = a_goal_context(target_weight=TargetWeight(70.0))
    context = a_progress_evaluation_context(
        progress_history=history,
        goal=goal,
        reference_date=start + timedelta(days=21),
    )
    result = ProgressEvaluationRuleEngine().evaluate(context)
    assert result.passed is True


# --- evaluate(): multiple findings at once ---


@pytest.mark.unit
def test_evaluating_a_stalled_history_triggers_body_weight_and_plateau() -> None:
    start = date(2026, 1, 1)
    # Flat around 78 (a plateau) while the target is 70 — the gap widens
    # slightly rather than narrowing, so BodyWeightRule should also fail.
    weights = [78.0, 78.4, 77.7, 78.2]
    history = [
        a_progress_context(
            progress_date=ProgressDate(start + timedelta(days=7 * i)),
            body_weight=BodyWeight(weight),
        )
        for i, weight in enumerate(weights)
    ]
    goal = a_goal_context(target_weight=TargetWeight(70.0))
    context = a_progress_evaluation_context(
        progress_history=history,
        goal=goal,
        reference_date=start + timedelta(days=21),
    )

    result = ProgressEvaluationRuleEngine().evaluate(context)

    assert result.passed is False
    assert RuleId("progress_evaluation.body_weight") in result.triggered_rules
    assert RuleId("progress_evaluation.plateau") in result.triggered_rules
    assert RuleId("progress_evaluation.consistency") not in result.triggered_rules


# --- determinism / side-effect freedom ---


@pytest.mark.unit
def test_evaluate_is_deterministic() -> None:
    context = a_progress_evaluation_context(progress_history=[a_progress_context()])
    engine = ProgressEvaluationRuleEngine()
    assert engine.evaluate(context) == engine.evaluate(context)


@pytest.mark.unit
def test_evaluate_does_not_mutate_the_context() -> None:
    history = (a_progress_context(),)
    context = a_progress_evaluation_context(progress_history=history)
    ProgressEvaluationRuleEngine().evaluate(context)
    assert context.progress_history == history
