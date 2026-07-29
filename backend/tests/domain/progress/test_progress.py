"""Tests for app/domain/progress/progress.py."""

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
from app.domain.progress.progress import Progress
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
from app.domain.shared_kernel.errors import DomainInvariantViolationError
from app.domain.user.identifiers import UserId
from tests.domain.progress.factories import a_fixed_clock, a_recorded_progress

# --- record() ---


@pytest.mark.unit
def test_record_exposes_the_required_fields_it_was_given() -> None:
    progress_id = ProgressId.generate()
    user_id = UserId.generate()
    progress = Progress.record(
        progress_id=progress_id,
        user_id=user_id,
        progress_date=ProgressDate(date(2026, 1, 1)),
        unit=MeasurementUnit.IMPERIAL,
        source=ProgressSource.SMART_SCALE,
        clock=a_fixed_clock(),
    )
    assert progress.id == progress_id
    assert progress.user_id == user_id
    assert progress.progress_date == ProgressDate(date(2026, 1, 1))
    assert progress.unit == MeasurementUnit.IMPERIAL
    assert progress.source == ProgressSource.SMART_SCALE


@pytest.mark.unit
def test_record_stamps_recorded_at_from_the_clock() -> None:
    clock = a_fixed_clock()
    progress = Progress.record(
        progress_id=ProgressId.generate(),
        user_id=UserId.generate(),
        progress_date=ProgressDate(date(2026, 1, 1)),
        unit=MeasurementUnit.METRIC,
        source=ProgressSource.MANUAL,
        clock=clock,
    )
    assert progress.recorded_at == clock.now()


@pytest.mark.unit
def test_record_defaults_every_optional_field_to_none_and_notes_to_empty() -> None:
    progress = a_recorded_progress()
    assert progress.body_weight is None
    assert progress.body_fat_percentage is None
    assert progress.lean_body_mass is None
    assert progress.muscle_mass is None
    assert progress.waist is None
    assert progress.chest is None
    assert progress.hip is None
    assert progress.arm is None
    assert progress.thigh is None
    assert progress.calf is None
    assert progress.neck is None
    assert progress.notes == ProgressNotes()
    assert progress.updated_at is None


@pytest.mark.unit
def test_record_accepts_every_optional_field_at_once() -> None:
    """The common real-world case: a single check-in where everything was
    captured together."""
    progress = Progress.record(
        progress_id=ProgressId.generate(),
        user_id=UserId.generate(),
        progress_date=ProgressDate(date(2026, 1, 1)),
        unit=MeasurementUnit.METRIC,
        source=ProgressSource.SMART_SCALE,
        clock=a_fixed_clock(),
        body_weight=BodyWeight(70.0),
        body_fat_percentage=BodyFatPercentage(18.0),
        lean_body_mass=LeanBodyMass(57.0),
        muscle_mass=MuscleMass(32.0),
        waist=WaistMeasurement(80.0),
        chest=ChestMeasurement(100.0),
        hip=HipMeasurement(95.0),
        arm=ArmMeasurement(35.0),
        thigh=ThighMeasurement(55.0),
        calf=CalfMeasurement(38.0),
        neck=NeckMeasurement(40.0),
        notes=ProgressNotes("Measured fasted."),
    )
    assert progress.body_weight == BodyWeight(70.0)
    assert progress.body_fat_percentage == BodyFatPercentage(18.0)
    assert progress.lean_body_mass == LeanBodyMass(57.0)
    assert progress.muscle_mass == MuscleMass(32.0)
    assert progress.waist == WaistMeasurement(80.0)
    assert progress.chest == ChestMeasurement(100.0)
    assert progress.hip == HipMeasurement(95.0)
    assert progress.arm == ArmMeasurement(35.0)
    assert progress.thigh == ThighMeasurement(55.0)
    assert progress.calf == CalfMeasurement(38.0)
    assert progress.neck == NeckMeasurement(40.0)
    assert progress.notes == ProgressNotes("Measured fasted.")


@pytest.mark.unit
def test_record_raises_a_progress_recorded_event() -> None:
    progress_id = ProgressId.generate()
    user_id = UserId.generate()
    progress_date = ProgressDate(date(2026, 1, 1))
    clock = a_fixed_clock()

    progress = Progress.record(
        progress_id=progress_id,
        user_id=user_id,
        progress_date=progress_date,
        unit=MeasurementUnit.METRIC,
        source=ProgressSource.MANUAL,
        clock=clock,
    )

    events = progress.pull_domain_events()
    assert len(events) == 1
    assert isinstance(events[0], ProgressRecorded)
    assert events[0].progress_id == progress_id
    assert events[0].user_id == user_id
    assert events[0].progress_date == progress_date
    assert events[0].unit == MeasurementUnit.METRIC
    assert events[0].source == ProgressSource.MANUAL
    assert events[0].occurred_at == clock.now()


@pytest.mark.unit
def test_record_raises_exactly_one_event_even_with_optional_fields_supplied() -> None:
    """Supplying body-composition/measurement values directly to record()
    does not also fire BodyCompositionUpdated/MeasurementsUpdated — those
    only fire from their own dedicated update methods."""
    progress = Progress.record(
        progress_id=ProgressId.generate(),
        user_id=UserId.generate(),
        progress_date=ProgressDate(date(2026, 1, 1)),
        unit=MeasurementUnit.METRIC,
        source=ProgressSource.MANUAL,
        clock=a_fixed_clock(),
        body_weight=BodyWeight(70.0),
        waist=WaistMeasurement(80.0),
        notes=ProgressNotes("hi"),
    )
    events = progress.pull_domain_events()
    assert len(events) == 1
    assert isinstance(events[0], ProgressRecorded)


@pytest.mark.unit
def test_record_generates_a_distinct_progress_each_time() -> None:
    assert a_recorded_progress().id != a_recorded_progress().id


# --- update_body_composition() ---


@pytest.mark.unit
def test_update_body_composition_sets_previously_unset_fields() -> None:
    progress = a_recorded_progress()
    progress.update_body_composition(body_weight=BodyWeight(70.0), clock=a_fixed_clock())
    assert progress.body_weight == BodyWeight(70.0)


@pytest.mark.unit
def test_update_body_composition_replaces_a_previously_set_field() -> None:
    progress = a_recorded_progress()
    clock = a_fixed_clock()
    progress.update_body_composition(body_weight=BodyWeight(70.0), clock=clock)
    progress.update_body_composition(body_weight=BodyWeight(69.0), clock=clock)
    assert progress.body_weight == BodyWeight(69.0)


@pytest.mark.unit
def test_update_body_composition_none_leaves_other_fields_unchanged() -> None:
    progress = a_recorded_progress()
    clock = a_fixed_clock()
    progress.update_body_composition(
        body_weight=BodyWeight(70.0), muscle_mass=MuscleMass(32.0), clock=clock
    )
    progress.update_body_composition(body_fat_percentage=BodyFatPercentage(18.0), clock=clock)
    assert progress.body_weight == BodyWeight(70.0)
    assert progress.muscle_mass == MuscleMass(32.0)
    assert progress.body_fat_percentage == BodyFatPercentage(18.0)


@pytest.mark.unit
def test_update_body_composition_stamps_updated_at() -> None:
    progress = a_recorded_progress()
    clock = a_fixed_clock()
    progress.update_body_composition(body_weight=BodyWeight(70.0), clock=clock)
    assert progress.updated_at == clock.now()


@pytest.mark.unit
def test_update_body_composition_records_event_with_full_resulting_snapshot() -> None:
    progress = a_recorded_progress()
    clock = a_fixed_clock()
    progress.update_body_composition(
        body_weight=BodyWeight(70.0), lean_body_mass=LeanBodyMass(57.0), clock=clock
    )
    progress.pull_domain_events()  # drain ProgressRecorded

    progress.update_body_composition(muscle_mass=MuscleMass(32.0), clock=clock)

    events = progress.pull_domain_events()
    assert len(events) == 1
    assert isinstance(events[0], BodyCompositionUpdated)
    assert events[0].body_weight == BodyWeight(70.0)
    assert events[0].lean_body_mass == LeanBodyMass(57.0)
    assert events[0].muscle_mass == MuscleMass(32.0)
    assert events[0].body_fat_percentage is None


@pytest.mark.unit
def test_update_body_composition_is_freely_callable_with_no_lifecycle_gate() -> None:
    """Progress has no status enum — nothing blocks calling update methods
    repeatedly, unlike Workout/Exercise/WorkoutSession's terminal-state
    guards. See progress.py's class docstring."""
    progress = a_recorded_progress()
    clock = a_fixed_clock()
    for weight in (70.0, 69.5, 69.0):
        progress.update_body_composition(body_weight=BodyWeight(weight), clock=clock)
    assert progress.body_weight == BodyWeight(69.0)


# --- update_measurements() ---


@pytest.mark.unit
def test_update_measurements_sets_previously_unset_fields() -> None:
    progress = a_recorded_progress()
    progress.update_measurements(waist=WaistMeasurement(80.0), clock=a_fixed_clock())
    assert progress.waist == WaistMeasurement(80.0)


@pytest.mark.unit
def test_update_measurements_replaces_a_previously_set_field() -> None:
    progress = a_recorded_progress()
    clock = a_fixed_clock()
    progress.update_measurements(waist=WaistMeasurement(80.0), clock=clock)
    progress.update_measurements(waist=WaistMeasurement(78.0), clock=clock)
    assert progress.waist == WaistMeasurement(78.0)


@pytest.mark.unit
def test_update_measurements_none_leaves_other_fields_unchanged() -> None:
    progress = a_recorded_progress()
    clock = a_fixed_clock()
    progress.update_measurements(
        waist=WaistMeasurement(80.0), chest=ChestMeasurement(100.0), clock=clock
    )
    progress.update_measurements(hip=HipMeasurement(95.0), clock=clock)
    assert progress.waist == WaistMeasurement(80.0)
    assert progress.chest == ChestMeasurement(100.0)
    assert progress.hip == HipMeasurement(95.0)


@pytest.mark.unit
def test_update_measurements_all_seven_fields_at_once() -> None:
    progress = a_recorded_progress()
    progress.update_measurements(
        waist=WaistMeasurement(80.0),
        chest=ChestMeasurement(100.0),
        hip=HipMeasurement(95.0),
        arm=ArmMeasurement(35.0),
        thigh=ThighMeasurement(55.0),
        calf=CalfMeasurement(38.0),
        neck=NeckMeasurement(40.0),
        clock=a_fixed_clock(),
    )
    assert progress.waist == WaistMeasurement(80.0)
    assert progress.chest == ChestMeasurement(100.0)
    assert progress.hip == HipMeasurement(95.0)
    assert progress.arm == ArmMeasurement(35.0)
    assert progress.thigh == ThighMeasurement(55.0)
    assert progress.calf == CalfMeasurement(38.0)
    assert progress.neck == NeckMeasurement(40.0)


@pytest.mark.unit
def test_update_measurements_stamps_updated_at() -> None:
    progress = a_recorded_progress()
    clock = a_fixed_clock()
    progress.update_measurements(waist=WaistMeasurement(80.0), clock=clock)
    assert progress.updated_at == clock.now()


@pytest.mark.unit
def test_update_measurements_records_event_with_full_resulting_snapshot() -> None:
    progress = a_recorded_progress()
    clock = a_fixed_clock()
    progress.update_measurements(waist=WaistMeasurement(80.0), clock=clock)
    progress.pull_domain_events()  # drain ProgressRecorded

    progress.update_measurements(chest=ChestMeasurement(100.0), clock=clock)

    events = progress.pull_domain_events()
    assert len(events) == 1
    assert isinstance(events[0], MeasurementsUpdated)
    assert events[0].waist == WaistMeasurement(80.0)
    assert events[0].chest == ChestMeasurement(100.0)
    assert events[0].hip is None


# --- update_notes() ---


@pytest.mark.unit
def test_update_notes_replaces_the_notes() -> None:
    progress = a_recorded_progress()
    progress.update_notes(ProgressNotes("Measured fasted."), clock=a_fixed_clock())
    assert progress.notes == ProgressNotes("Measured fasted.")


@pytest.mark.unit
def test_update_notes_accepts_an_explicitly_empty_value() -> None:
    progress = a_recorded_progress()
    clock = a_fixed_clock()
    progress.update_notes(ProgressNotes("something"), clock=clock)
    progress.update_notes(ProgressNotes(""), clock=clock)
    assert progress.notes == ProgressNotes("")


@pytest.mark.unit
def test_update_notes_stamps_updated_at() -> None:
    progress = a_recorded_progress()
    clock = a_fixed_clock()
    progress.update_notes(ProgressNotes("x"), clock=clock)
    assert progress.updated_at == clock.now()


@pytest.mark.unit
def test_update_notes_records_a_progress_notes_updated_event() -> None:
    progress = a_recorded_progress()
    clock = a_fixed_clock()
    notes = ProgressNotes("Measured fasted.")

    progress.update_notes(notes, clock=clock)

    events = progress.pull_domain_events()
    assert len(events) == 2  # ProgressRecorded, then ProgressNotesUpdated
    assert isinstance(events[-1], ProgressNotesUpdated)
    assert events[-1].notes == notes
    assert events[-1].occurred_at == clock.now()


# --- __init__ construction (repository rehydration path) ---


@pytest.mark.unit
def test_constructor_rejects_a_naive_recorded_at() -> None:
    with pytest.raises(DomainInvariantViolationError, match="timezone-aware"):
        Progress(
            ProgressId.generate(),
            user_id=UserId.generate(),
            progress_date=ProgressDate(date(2026, 1, 1)),
            unit=MeasurementUnit.METRIC,
            source=ProgressSource.MANUAL,
            recorded_at=datetime(2026, 1, 1),  # deliberately naive
        )


@pytest.mark.unit
def test_constructor_rehydrates_an_existing_record_with_no_side_effects() -> None:
    """The path a repository uses to reconstruct a Progress already in
    storage — no event should be raised."""
    progress = Progress(
        ProgressId.generate(),
        user_id=UserId.generate(),
        progress_date=ProgressDate(date(2026, 1, 1)),
        unit=MeasurementUnit.METRIC,
        source=ProgressSource.MANUAL,
        recorded_at=datetime.now(timezone.utc),
        body_weight=BodyWeight(70.0),
    )
    assert progress.pull_domain_events() == []
    assert progress.body_weight == BodyWeight(70.0)


@pytest.mark.unit
def test_constructor_accepts_every_explicit_field() -> None:
    now = datetime.now(timezone.utc)
    progress = Progress(
        ProgressId.generate(),
        user_id=UserId.generate(),
        progress_date=ProgressDate(date(2026, 1, 1)),
        unit=MeasurementUnit.IMPERIAL,
        source=ProgressSource.CALCULATED,
        recorded_at=now,
        body_weight=BodyWeight(70.0),
        body_fat_percentage=BodyFatPercentage(18.0),
        lean_body_mass=LeanBodyMass(57.0),
        muscle_mass=MuscleMass(32.0),
        waist=WaistMeasurement(80.0),
        chest=ChestMeasurement(100.0),
        hip=HipMeasurement(95.0),
        arm=ArmMeasurement(35.0),
        thigh=ThighMeasurement(55.0),
        calf=CalfMeasurement(38.0),
        neck=NeckMeasurement(40.0),
        notes=ProgressNotes("Rehydrated."),
        updated_at=now,
    )
    assert progress.unit == MeasurementUnit.IMPERIAL
    assert progress.source == ProgressSource.CALCULATED
    assert progress.body_weight == BodyWeight(70.0)
    assert progress.body_fat_percentage == BodyFatPercentage(18.0)
    assert progress.lean_body_mass == LeanBodyMass(57.0)
    assert progress.muscle_mass == MuscleMass(32.0)
    assert progress.waist == WaistMeasurement(80.0)
    assert progress.chest == ChestMeasurement(100.0)
    assert progress.hip == HipMeasurement(95.0)
    assert progress.arm == ArmMeasurement(35.0)
    assert progress.thigh == ThighMeasurement(55.0)
    assert progress.calf == CalfMeasurement(38.0)
    assert progress.neck == NeckMeasurement(40.0)
    assert progress.notes == ProgressNotes("Rehydrated.")
    assert progress.updated_at == now
