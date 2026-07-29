"""Tests for app/domain/rules/recommendation.py."""

from dataclasses import FrozenInstanceError

import pytest

from app.domain.rules.recommendation import Recommendation
from app.domain.rules.severity import RecommendationSeverity
from app.domain.shared_kernel.errors import DomainInvariantViolationError


@pytest.mark.unit
def test_recommendation_exposes_severity_and_message() -> None:
    recommendation = Recommendation(
        severity=RecommendationSeverity.WARNING, message="Consider resting today."
    )
    assert recommendation.severity == RecommendationSeverity.WARNING
    assert recommendation.message == "Consider resting today."


@pytest.mark.unit
def test_recommendation_rejects_an_empty_message() -> None:
    with pytest.raises(DomainInvariantViolationError, match="must not be empty"):
        Recommendation(severity=RecommendationSeverity.INFO, message="")


@pytest.mark.unit
def test_recommendation_is_immutable() -> None:
    recommendation = Recommendation(severity=RecommendationSeverity.INFO, message="Hi")
    with pytest.raises(FrozenInstanceError):
        recommendation.message = "Changed"  # type: ignore[misc]


@pytest.mark.unit
def test_recommendation_equality_is_by_value() -> None:
    a = Recommendation(severity=RecommendationSeverity.INFO, message="Hi")
    b = Recommendation(severity=RecommendationSeverity.INFO, message="Hi")
    c = Recommendation(severity=RecommendationSeverity.WARNING, message="Hi")
    assert a == b
    assert a != c
