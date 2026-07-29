"""Tests for app/domain/progress/events.py.

Immutability, `event_id` auto-generation, and `occurred_at` timezone
enforcement are `DomainEvent` base behavior, already fully covered by
`tests/domain/shared_kernel/test_events.py`. This file only proves each
Progress-specific event carries the fields it's supposed to.
"""

from datetime import date, datetime, timezone

import pytest

from app.domain.progress.enums import MeasurementUnit, ProgressSource
from app.domain.progress.events import (
    BodyCompositionUpdated,
    MeasurementsUpdated,
    ProgressNotesUpdated,
    ProgressRecorded,
)
from app.domain.progress.identifiers import ProgressId
from app.domain.progress.value_objects import (
    ArmMeasurement,
    BodyFatPercentage,
    BodyWeight,
    CalfMeasurement,
    ChestMeasurement,
    HipMeasurement,
    LeanBodyMass,
    MuscleMass,
    NeckMeasurement,
    ProgressDate,
    ProgressNotes,
    ThighMeasurement,
    WaistMeasurement,
)
from app.domain.user.identifiers import UserId


@pytest.mark.unit
def test_progress_recorded_carries_identifying_fields() -> None:
    progress_id = ProgressId.generate()
    user_id = UserId.generate()
    progress_date = ProgressDate(date(2026, 1, 1))
    event = ProgressRecorded(
        occurred_at=datetime.now(timezone.utc),
        progress_id=progress_id,
        user_id=user_id,
        progress_date=progress_date,
        unit=MeasurementUnit.METRIC,
        source=ProgressSource.MANUAL,
    )
    assert event.progress_id == progress_id
    assert event.user_id == user_id
    assert event.progress_date == progress_date
    assert event.unit == MeasurementUnit.METRIC
    assert event.source == ProgressSource.MANUAL


@pytest.mark.unit
def test_body_composition_updated_carries_all_four_fields() -> None:
    progress_id = ProgressId.generate()
    body_weight = BodyWeight(70.0)
    body_fat = BodyFatPercentage(18.0)
    lean_mass = LeanBodyMass(57.0)
    muscle_mass = MuscleMass(32.0)
    event = BodyCompositionUpdated(
        occurred_at=datetime.now(timezone.utc),
        progress_id=progress_id,
        user_id=UserId.generate(),
        body_weight=body_weight,
        body_fat_percentage=body_fat,
        lean_body_mass=lean_mass,
        muscle_mass=muscle_mass,
    )
    assert event.progress_id == progress_id
    assert event.body_weight == body_weight
    assert event.body_fat_percentage == body_fat
    assert event.lean_body_mass == lean_mass
    assert event.muscle_mass == muscle_mass


@pytest.mark.unit
def test_body_composition_updated_allows_any_field_to_be_none() -> None:
    event = BodyCompositionUpdated(
        occurred_at=datetime.now(timezone.utc),
        progress_id=ProgressId.generate(),
        user_id=UserId.generate(),
        body_weight=None,
        body_fat_percentage=None,
        lean_body_mass=None,
        muscle_mass=None,
    )
    assert event.body_weight is None
    assert event.muscle_mass is None


@pytest.mark.unit
def test_measurements_updated_carries_all_seven_fields() -> None:
    progress_id = ProgressId.generate()
    waist = WaistMeasurement(80.0)
    chest = ChestMeasurement(100.0)
    hip = HipMeasurement(95.0)
    arm = ArmMeasurement(35.0)
    thigh = ThighMeasurement(55.0)
    calf = CalfMeasurement(38.0)
    neck = NeckMeasurement(40.0)
    event = MeasurementsUpdated(
        occurred_at=datetime.now(timezone.utc),
        progress_id=progress_id,
        user_id=UserId.generate(),
        waist=waist,
        chest=chest,
        hip=hip,
        arm=arm,
        thigh=thigh,
        calf=calf,
        neck=neck,
    )
    assert event.progress_id == progress_id
    assert event.waist == waist
    assert event.chest == chest
    assert event.hip == hip
    assert event.arm == arm
    assert event.thigh == thigh
    assert event.calf == calf
    assert event.neck == neck


@pytest.mark.unit
def test_progress_notes_updated_carries_the_full_new_notes() -> None:
    progress_id = ProgressId.generate()
    notes = ProgressNotes("Measured fasted.")
    event = ProgressNotesUpdated(
        occurred_at=datetime.now(timezone.utc),
        progress_id=progress_id,
        user_id=UserId.generate(),
        notes=notes,
    )
    assert event.progress_id == progress_id
    assert event.notes == notes
