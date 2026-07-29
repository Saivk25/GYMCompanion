"""Tests for app/domain/progress/enums.py."""

import pytest

from app.domain.progress.enums import MeasurementUnit, ProgressSource


@pytest.mark.unit
def test_measurement_unit_has_exactly_two_members() -> None:
    assert {member.value for member in MeasurementUnit} == {"metric", "imperial"}


@pytest.mark.unit
def test_measurement_unit_is_a_str_subclass() -> None:
    assert isinstance(MeasurementUnit.METRIC, str)
    assert MeasurementUnit.METRIC.value == "metric"


@pytest.mark.unit
def test_progress_source_has_exactly_three_members() -> None:
    assert {member.value for member in ProgressSource} == {
        "manual",
        "smart_scale",
        "calculated",
    }


@pytest.mark.unit
def test_progress_source_is_a_str_subclass() -> None:
    assert isinstance(ProgressSource.MANUAL, str)
    assert ProgressSource.MANUAL.value == "manual"
