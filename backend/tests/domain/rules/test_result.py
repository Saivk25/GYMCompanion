"""Tests for app/domain/rules/result.py."""

from dataclasses import FrozenInstanceError

import pytest

from app.domain.rules.recommendation import Recommendation
from app.domain.rules.result import RuleId, RuleResult
from app.domain.rules.severity import RecommendationSeverity
from app.domain.shared_kernel.errors import DomainInvariantViolationError

# --- RuleId ---


@pytest.mark.unit
def test_rule_id_accepts_a_non_empty_string() -> None:
    assert RuleId("safety.contraindication_check").value == "safety.contraindication_check"


@pytest.mark.unit
def test_rule_id_rejects_an_empty_string() -> None:
    with pytest.raises(DomainInvariantViolationError, match="must not be empty"):
        RuleId("")


@pytest.mark.unit
def test_rule_id_is_immutable() -> None:
    rule_id = RuleId("test.rule")
    with pytest.raises(FrozenInstanceError):
        rule_id.value = "changed"  # type: ignore[misc]


@pytest.mark.unit
def test_rule_id_equality_is_by_value() -> None:
    assert RuleId("test.rule") == RuleId("test.rule")
    assert RuleId("test.rule") != RuleId("other.rule")


@pytest.mark.unit
def test_rule_id_str_returns_the_raw_value() -> None:
    assert str(RuleId("test.rule")) == "test.rule"


@pytest.mark.unit
def test_rule_id_is_not_an_entity_id() -> None:
    """A deliberate architectural difference from every aggregate's own
    id type — see the module docstring for why."""
    from app.domain.shared_kernel.identifiers import EntityId

    assert not issubclass(RuleId, EntityId)


# --- RuleResult ---


@pytest.mark.unit
def test_rule_result_exposes_every_field() -> None:
    recommendation = Recommendation(severity=RecommendationSeverity.WARNING, message="Rest more.")
    rule_id = RuleId("test.rule")
    result = RuleResult(
        passed=False,
        severity=RecommendationSeverity.WARNING,
        explanation="Something triggered.",
        recommendations=(recommendation,),
        triggered_rules=(rule_id,),
    )
    assert result.passed is False
    assert result.severity == RecommendationSeverity.WARNING
    assert result.explanation == "Something triggered."
    assert result.recommendations == (recommendation,)
    assert result.triggered_rules == (rule_id,)


@pytest.mark.unit
def test_rule_result_defaults_recommendations_and_triggered_rules_to_empty() -> None:
    result = RuleResult(
        passed=True,
        severity=RecommendationSeverity.INFO,
        explanation="All good.",
    )
    assert result.recommendations == ()
    assert result.triggered_rules == ()


@pytest.mark.unit
def test_rule_result_rejects_an_empty_explanation() -> None:
    with pytest.raises(DomainInvariantViolationError, match="must not be empty"):
        RuleResult(passed=True, severity=RecommendationSeverity.INFO, explanation="")


@pytest.mark.unit
def test_rule_result_is_immutable() -> None:
    result = RuleResult(passed=True, severity=RecommendationSeverity.INFO, explanation="ok")
    with pytest.raises(FrozenInstanceError):
        result.passed = False  # type: ignore[misc]


@pytest.mark.unit
def test_rule_result_equality_is_by_value() -> None:
    a = RuleResult(passed=True, severity=RecommendationSeverity.INFO, explanation="ok")
    b = RuleResult(passed=True, severity=RecommendationSeverity.INFO, explanation="ok")
    c = RuleResult(passed=False, severity=RecommendationSeverity.INFO, explanation="ok")
    assert a == b
    assert a != c


@pytest.mark.unit
def test_two_rule_result_instances_do_not_share_default_tuples() -> None:
    """Guards against a mutable-default-style bug: each instance's default
    `recommendations`/`triggered_rules` must be its own empty tuple, not a
    single object shared (and potentially mutated) across instances —
    tuples are immutable so this can't actually go wrong, but the
    `field(default_factory=tuple)` construction is what this test pins
    down as intentional, not `field(default=())`, which would also work
    for an immutable type but is the less idiomatic dataclass spelling.
    """
    a = RuleResult(passed=True, severity=RecommendationSeverity.INFO, explanation="ok")
    b = RuleResult(passed=True, severity=RecommendationSeverity.INFO, explanation="ok")
    assert a.recommendations == b.recommendations
    assert a.triggered_rules == b.triggered_rules
