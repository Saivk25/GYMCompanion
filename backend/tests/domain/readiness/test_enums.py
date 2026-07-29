"""Tests for app/domain/readiness/enums.py."""

import pytest

from app.domain.readiness.enums import ReadinessSource


@pytest.mark.unit
def test_readiness_source_has_exactly_three_members() -> None:
    assert {member.value for member in ReadinessSource} == {
        "manual",
        "wearable",
        "imported",
    }


@pytest.mark.unit
def test_readiness_source_is_a_str_subclass() -> None:
    assert isinstance(ReadinessSource.MANUAL, str)
    assert ReadinessSource.MANUAL.value == "manual"
