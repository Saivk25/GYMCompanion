"""Tests for app/application/readiness/dto/readiness_dto.py."""

from dataclasses import FrozenInstanceError

import pytest

from app.application.readiness.dto.readiness_dto import ReadinessDTO
from app.domain.readiness.value_objects import EnergyLevel, SleepQuality
from tests.application.readiness.factories import a_fixed_clock, a_recorded_readiness


@pytest.mark.unit
def test_from_readiness_maps_every_field_for_a_freshly_recorded_check_in() -> None:
    readiness = a_recorded_readiness()

    dto = ReadinessDTO.from_readiness(readiness)

    assert dto.readiness_id == readiness.id
    assert dto.user_id == readiness.user_id
    assert dto.readiness_date == readiness.readiness_date
    assert dto.recorded_at == readiness.recorded_at
    assert dto.source is None
    assert dto.sleep_duration is None
    assert dto.sleep_quality is None
    assert dto.energy_level is None
    assert dto.stress_level is None
    assert dto.soreness_level is None
    assert dto.resting_heart_rate is None
    assert dto.heart_rate_variability is None
    assert dto.notes == readiness.notes
    assert dto.updated_at is None


@pytest.mark.unit
def test_from_readiness_reflects_updated_sleep_and_recovery_metrics() -> None:
    readiness = a_recorded_readiness()
    readiness.update_sleep(sleep_quality=SleepQuality(8), clock=a_fixed_clock())
    readiness.update_recovery_metrics(energy_level=EnergyLevel(6), clock=a_fixed_clock())

    dto = ReadinessDTO.from_readiness(readiness)

    assert dto.sleep_quality == SleepQuality(8)
    assert dto.energy_level == EnergyLevel(6)
    assert dto.updated_at is not None


@pytest.mark.unit
def test_readiness_dto_is_immutable() -> None:
    dto = ReadinessDTO.from_readiness(a_recorded_readiness())
    with pytest.raises(FrozenInstanceError):
        dto.energy_level = EnergyLevel(5)  # type: ignore[misc]
