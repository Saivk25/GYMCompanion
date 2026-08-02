"""Tests for app/application/progress/dto/progress_dto.py."""

from dataclasses import FrozenInstanceError

import pytest

from app.application.progress.dto.progress_dto import ProgressDTO
from app.domain.progress.value_objects import BodyWeight, ProgressNotes, WaistMeasurement
from tests.application.progress.factories import a_fixed_clock, a_recorded_progress


@pytest.mark.unit
def test_from_progress_maps_every_field_for_a_freshly_recorded_entry() -> None:
    progress = a_recorded_progress()

    dto = ProgressDTO.from_progress(progress)

    assert dto.progress_id == progress.id
    assert dto.user_id == progress.user_id
    assert dto.progress_date == progress.progress_date
    assert dto.unit == progress.unit
    assert dto.source == progress.source
    assert dto.recorded_at == progress.recorded_at
    assert dto.body_weight is None
    assert dto.body_fat_percentage is None
    assert dto.lean_body_mass is None
    assert dto.muscle_mass is None
    assert dto.waist is None
    assert dto.chest is None
    assert dto.hip is None
    assert dto.arm is None
    assert dto.thigh is None
    assert dto.calf is None
    assert dto.neck is None
    assert dto.notes == progress.notes
    assert dto.updated_at is None


@pytest.mark.unit
def test_from_progress_reflects_updated_body_composition_and_measurements() -> None:
    progress = a_recorded_progress()
    progress.update_body_composition(body_weight=BodyWeight(80.0), clock=a_fixed_clock())
    progress.update_measurements(waist=WaistMeasurement(85.0), clock=a_fixed_clock())

    dto = ProgressDTO.from_progress(progress)

    assert dto.body_weight == BodyWeight(80.0)
    assert dto.waist == WaistMeasurement(85.0)
    assert dto.updated_at is not None


@pytest.mark.unit
def test_progress_dto_is_immutable() -> None:
    dto = ProgressDTO.from_progress(a_recorded_progress())
    with pytest.raises(FrozenInstanceError):
        dto.notes = ProgressNotes("changed")  # type: ignore[misc]
