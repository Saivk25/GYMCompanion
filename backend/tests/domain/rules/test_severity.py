"""Tests for app/domain/rules/severity.py."""

import pytest

from app.domain.rules.severity import RecommendationSeverity, severity_rank


@pytest.mark.unit
def test_recommendation_severity_has_exactly_four_members() -> None:
    assert {member.value for member in RecommendationSeverity} == {
        "info",
        "advisory",
        "warning",
        "critical",
    }


@pytest.mark.unit
def test_recommendation_severity_is_a_str_subclass() -> None:
    assert isinstance(RecommendationSeverity.INFO, str)
    assert RecommendationSeverity.INFO.value == "info"


@pytest.mark.unit
def test_severity_rank_orders_info_lowest_and_critical_highest() -> None:
    assert severity_rank(RecommendationSeverity.INFO) < severity_rank(
        RecommendationSeverity.ADVISORY
    )
    assert severity_rank(RecommendationSeverity.ADVISORY) < severity_rank(
        RecommendationSeverity.WARNING
    )
    assert severity_rank(RecommendationSeverity.WARNING) < severity_rank(
        RecommendationSeverity.CRITICAL
    )


@pytest.mark.unit
def test_severity_rank_is_not_lexicographic() -> None:
    """A guard against accidentally relying on `str.__lt__` instead of
    `severity_rank`: "critical" sorts before "warning" lexicographically,
    which would be the wrong ordering for this scale."""
    assert severity_rank(RecommendationSeverity.CRITICAL) > severity_rank(
        RecommendationSeverity.WARNING
    )


@pytest.mark.unit
def test_severity_rank_covers_every_member() -> None:
    for member in RecommendationSeverity:
        assert isinstance(severity_rank(member), int)
