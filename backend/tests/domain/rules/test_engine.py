"""Tests for app/domain/rules/engine.py."""

import pytest

from app.domain.rules.engine import RuleEngine
from app.domain.rules.recommendation import Recommendation
from app.domain.rules.result import RuleId
from app.domain.rules.severity import RecommendationSeverity
from tests.domain.rules.factories import AlwaysFailRule, AlwaysPassRule, DummyContext

# --- construction ---


@pytest.mark.unit
def test_rules_property_exposes_the_rules_given_at_construction() -> None:
    rule_a = AlwaysPassRule(rule_id=RuleId("a"))
    rule_b = AlwaysPassRule(rule_id=RuleId("b"))
    engine = RuleEngine([rule_a, rule_b])
    assert engine.rules == (rule_a, rule_b)


@pytest.mark.unit
def test_rules_is_a_tuple_even_when_given_a_list() -> None:
    engine = RuleEngine([AlwaysPassRule()])
    assert isinstance(engine.rules, tuple)


# --- evaluate(): empty rule set ---


@pytest.mark.unit
def test_evaluating_an_empty_rule_set_passes_with_no_findings() -> None:
    engine: RuleEngine[DummyContext] = RuleEngine([])
    result = engine.evaluate(DummyContext())
    assert result.passed is True
    assert result.severity == RecommendationSeverity.INFO
    assert result.explanation == "No rules triggered."
    assert result.recommendations == ()
    assert result.triggered_rules == ()


# --- evaluate(): all pass ---


@pytest.mark.unit
def test_evaluate_passes_when_every_rule_passes() -> None:
    engine = RuleEngine([AlwaysPassRule(rule_id=RuleId("a")), AlwaysPassRule(rule_id=RuleId("b"))])
    result = engine.evaluate(DummyContext())
    assert result.passed is True
    assert result.triggered_rules == ()
    assert result.explanation == "No rules triggered."


@pytest.mark.unit
def test_evaluate_flattens_recommendations_from_passing_rules_too() -> None:
    recommendation = Recommendation(severity=RecommendationSeverity.INFO, message="Nice work.")
    engine = RuleEngine([AlwaysPassRule(recommendations=(recommendation,))])
    result = engine.evaluate(DummyContext())
    assert result.recommendations == (recommendation,)


# --- evaluate(): some fail ---


@pytest.mark.unit
def test_evaluate_fails_when_any_rule_fails() -> None:
    engine = RuleEngine([AlwaysPassRule(rule_id=RuleId("a")), AlwaysFailRule(rule_id=RuleId("b"))])
    result = engine.evaluate(DummyContext())
    assert result.passed is False
    assert result.triggered_rules == (RuleId("b"),)


@pytest.mark.unit
def test_evaluate_collects_triggered_rules_in_evaluation_order() -> None:
    engine = RuleEngine(
        [
            AlwaysFailRule(rule_id=RuleId("first")),
            AlwaysPassRule(rule_id=RuleId("second")),
            AlwaysFailRule(rule_id=RuleId("third")),
        ]
    )
    result = engine.evaluate(DummyContext())
    assert result.triggered_rules == (RuleId("first"), RuleId("third"))


@pytest.mark.unit
def test_evaluate_joins_triggered_explanations() -> None:
    engine = RuleEngine(
        [
            AlwaysFailRule(rule_id=RuleId("a"), explanation="first problem"),
            AlwaysFailRule(rule_id=RuleId("b"), explanation="second problem"),
        ]
    )
    result = engine.evaluate(DummyContext())
    assert result.explanation == "first problem; second problem"


@pytest.mark.unit
def test_evaluate_reports_the_highest_severity_among_triggered_rules() -> None:
    engine = RuleEngine(
        [
            AlwaysFailRule(rule_id=RuleId("a"), severity=RecommendationSeverity.ADVISORY),
            AlwaysFailRule(rule_id=RuleId("b"), severity=RecommendationSeverity.CRITICAL),
            AlwaysFailRule(rule_id=RuleId("c"), severity=RecommendationSeverity.WARNING),
        ]
    )
    result = engine.evaluate(DummyContext())
    assert result.severity == RecommendationSeverity.CRITICAL


@pytest.mark.unit
def test_evaluate_ignores_a_passing_rules_severity_for_aggregation() -> None:
    """A passing CRITICAL-severity rule must not make the overall result
    CRITICAL — only triggered results count toward the aggregate
    severity."""
    engine = RuleEngine(
        [
            AlwaysPassRule(severity=RecommendationSeverity.CRITICAL),
            AlwaysFailRule(rule_id=RuleId("b"), severity=RecommendationSeverity.ADVISORY),
        ]
    )
    result = engine.evaluate(DummyContext())
    assert result.severity == RecommendationSeverity.ADVISORY


@pytest.mark.unit
def test_evaluate_flattens_recommendations_from_all_rules() -> None:
    passing_recommendation = Recommendation(severity=RecommendationSeverity.INFO, message="Good.")
    failing_recommendation = Recommendation(
        severity=RecommendationSeverity.WARNING, message="Careful."
    )
    engine = RuleEngine(
        [
            AlwaysPassRule(recommendations=(passing_recommendation,)),
            AlwaysFailRule(rule_id=RuleId("b"), recommendations=(failing_recommendation,)),
        ]
    )
    result = engine.evaluate(DummyContext())
    assert result.recommendations == (passing_recommendation, failing_recommendation)


# --- determinism ---


@pytest.mark.unit
def test_evaluate_is_deterministic_for_an_equal_context() -> None:
    engine = RuleEngine([AlwaysPassRule(rule_id=RuleId("a")), AlwaysFailRule(rule_id=RuleId("b"))])
    first = engine.evaluate(DummyContext(value=1))
    second = engine.evaluate(DummyContext(value=1))
    assert first == second


@pytest.mark.unit
def test_evaluate_does_not_mutate_the_context() -> None:
    context = DummyContext(value=7)
    engine = RuleEngine([AlwaysFailRule()])
    engine.evaluate(context)
    assert context.value == 7
