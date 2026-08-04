"""Tests for app/application/shared/advisory_warnings.py."""

import pytest

from app.application.shared.advisory_warnings import advisory_warnings
from app.domain.rules.recommendation import Recommendation
from app.domain.rules.result import RuleResult
from app.domain.rules.severity import RecommendationSeverity


def _a_result(*recommendations: Recommendation, passed: bool = False) -> RuleResult:
    return RuleResult(
        passed=passed,
        severity=RecommendationSeverity.WARNING,
        explanation="a rule evaluated",
        recommendations=recommendations,
    )


@pytest.mark.unit
def test_formats_a_single_recommendation_as_severity_bracket_message() -> None:
    result = _a_result(
        Recommendation(
            severity=RecommendationSeverity.ADVISORY, message="consider adding more fiber"
        )
    )

    warnings = advisory_warnings(result)

    assert warnings == ("[advisory] consider adding more fiber",)


@pytest.mark.unit
def test_formats_every_recommendation_in_order() -> None:
    result = _a_result(
        Recommendation(severity=RecommendationSeverity.WARNING, message="first"),
        Recommendation(severity=RecommendationSeverity.CRITICAL, message="second"),
    )

    warnings = advisory_warnings(result)

    assert warnings == ("[warning] first", "[critical] second")


@pytest.mark.unit
def test_returns_an_empty_tuple_when_there_are_no_recommendations() -> None:
    result = _a_result(passed=True)

    warnings = advisory_warnings(result)

    assert warnings == ()


@pytest.mark.unit
def test_returns_a_tuple_of_str() -> None:
    result = _a_result(Recommendation(severity=RecommendationSeverity.INFO, message="note"))

    warnings = advisory_warnings(result)

    assert isinstance(warnings, tuple)
    assert all(isinstance(warning, str) for warning in warnings)
