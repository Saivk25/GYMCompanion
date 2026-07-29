"""Tests for app/domain/progress/context.py."""

from dataclasses import FrozenInstanceError

import pytest

from app.domain.progress.context import ProgressContext
from app.domain.progress.enums import MeasurementUnit, ProgressSource
from app.domain.progress.value_objects import BodyWeight, ProgressNotes, WaistMeasurement
from tests.domain.progress.factories import a_fixed_clock, a_recorded_progress


@pytest.mark.unit
def test_from_progress_snapshots_every_relevant_field() -> None:
    progress = a_recorded_progress()

    context = ProgressContext.from_progress(progress)

    assert context.progress_id == progress.id
    assert context.user_id == progress.user_id
    assert context.progress_date == progress.progress_date
    assert context.unit == MeasurementUnit.METRIC
    assert context.source == ProgressSource.MANUAL
    assert context.body_weight is None
    assert context.body_fat_percentage is None
    assert context.lean_body_mass is None
    assert context.muscle_mass is None
    assert context.waist is None
    assert context.chest is None
    assert context.hip is None
    assert context.arm is None
    assert context.thigh is None
    assert context.calf is None
    assert context.neck is None
    assert context.notes == ProgressNotes()


@pytest.mark.unit
def test_is_immutable() -> None:
    progress = a_recorded_progress()
    context = ProgressContext.from_progress(progress)
    with pytest.raises(FrozenInstanceError):
        context.notes = ProgressNotes("changed")  # type: ignore[misc]


@pytest.mark.unit
def test_does_not_reflect_later_mutations_of_the_source_progress() -> None:
    progress = a_recorded_progress()
    context = ProgressContext.from_progress(progress)

    progress.update_body_composition(body_weight=BodyWeight(70.0), clock=a_fixed_clock())
    progress.update_measurements(waist=WaistMeasurement(80.0), clock=a_fixed_clock())

    assert context.body_weight is None
    assert context.waist is None
    assert progress.body_weight == BodyWeight(70.0)
    assert progress.waist == WaistMeasurement(80.0)
