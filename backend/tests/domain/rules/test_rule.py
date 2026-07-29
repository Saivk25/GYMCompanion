"""Tests for app/domain/rules/rule.py."""

import pytest

from app.domain.rules.recommendation import Recommendation
from app.domain.rules.result import RuleId, RuleResult
from app.domain.rules.rule import Rule
from app.domain.rules.severity import RecommendationSeverity
from app.domain.shared_kernel.errors import DomainInvariantViolationError
from tests.domain.rules.factories import (
    AlwaysFailRule,
    AlwaysPassRule,
    DummyContext,
    ThresholdRule,
)

# --- Rule is abstract ---


@pytest.mark.unit
def test_rule_cannot_be_instantiated_directly() -> None:
    with pytest.raises(TypeError):
        Rule(  # type: ignore[abstract]
            rule_id=RuleId("test.rule"),
            name="Test",
            description="A test rule.",
            severity=RecommendationSeverity.INFO,
        )


# --- constructor / properties ---


@pytest.mark.unit
def test_a_concrete_rule_exposes_id_name_description_severity() -> None:
    rule = AlwaysPassRule(rule_id=RuleId("test.example"), severity=RecommendationSeverity.ADVISORY)
    assert rule.id == RuleId("test.example")
    assert rule.name == "Always Pass"
    assert rule.description == "A rule that always passes, for testing."
    assert rule.severity == RecommendationSeverity.ADVISORY


@pytest.mark.unit
def test_rule_name_cannot_be_empty() -> None:
    class _BlankNameRule(Rule[DummyContext]):
        def __init__(self) -> None:
            super().__init__(
                rule_id=RuleId("test.blank"),
                name="",
                description="A rule.",
                severity=RecommendationSeverity.INFO,
            )

        def evaluate(self, context: DummyContext) -> RuleResult:  # pragma: no cover — never reached
            raise NotImplementedError

    with pytest.raises(DomainInvariantViolationError, match="rule name must not be empty"):
        _BlankNameRule()


@pytest.mark.unit
def test_rule_description_cannot_be_empty() -> None:
    class _BlankDescriptionRule(Rule[DummyContext]):
        def __init__(self) -> None:
            super().__init__(
                rule_id=RuleId("test.blank"),
                name="Name",
                description="",
                severity=RecommendationSeverity.INFO,
            )

        def evaluate(self, context: DummyContext) -> RuleResult:  # pragma: no cover — never reached
            raise NotImplementedError

    with pytest.raises(DomainInvariantViolationError, match="rule description must not be empty"):
        _BlankDescriptionRule()


# --- evaluate() / _pass() / _fail() ---


@pytest.mark.unit
def test_pass_produces_a_passed_result_with_no_triggered_rules() -> None:
    rule = AlwaysPassRule()
    result = rule.evaluate(DummyContext())
    assert result.passed is True
    assert result.triggered_rules == ()
    assert result.explanation == "always passes"


@pytest.mark.unit
def test_pass_stamps_the_rules_own_severity() -> None:
    rule = AlwaysPassRule(severity=RecommendationSeverity.CRITICAL)
    result = rule.evaluate(DummyContext())
    assert result.severity == RecommendationSeverity.CRITICAL


@pytest.mark.unit
def test_pass_can_still_carry_recommendations() -> None:
    recommendation = Recommendation(severity=RecommendationSeverity.INFO, message="Nice work.")
    rule = AlwaysPassRule(recommendations=(recommendation,))
    result = rule.evaluate(DummyContext())
    assert result.passed is True
    assert result.recommendations == (recommendation,)


@pytest.mark.unit
def test_fail_produces_a_failed_result_with_its_own_id_as_triggered() -> None:
    rule_id = RuleId("test.example_fail")
    rule = AlwaysFailRule(rule_id=rule_id)
    result = rule.evaluate(DummyContext())
    assert result.passed is False
    assert result.triggered_rules == (rule_id,)


@pytest.mark.unit
def test_fail_stamps_the_rules_own_severity() -> None:
    rule = AlwaysFailRule(severity=RecommendationSeverity.WARNING)
    result = rule.evaluate(DummyContext())
    assert result.severity == RecommendationSeverity.WARNING


@pytest.mark.unit
def test_fail_carries_the_given_explanation_and_recommendations() -> None:
    recommendation = Recommendation(severity=RecommendationSeverity.WARNING, message="Rest.")
    rule = AlwaysFailRule(explanation="something is wrong", recommendations=(recommendation,))
    result = rule.evaluate(DummyContext())
    assert result.explanation == "something is wrong"
    assert result.recommendations == (recommendation,)


@pytest.mark.unit
def test_a_rule_that_branches_on_context() -> None:
    rule = ThresholdRule(threshold=10)
    assert rule.evaluate(DummyContext(value=10)).passed is True
    assert rule.evaluate(DummyContext(value=9)).passed is False


@pytest.mark.unit
def test_evaluate_is_deterministic_for_an_equal_context() -> None:
    rule = ThresholdRule(threshold=5)
    first = rule.evaluate(DummyContext(value=3))
    second = rule.evaluate(DummyContext(value=3))
    assert first == second
