"""Tests for app/domain/readiness/readiness.py."""

from datetime import date, datetime, timedelta, timezone

import pytest

from app.domain.readiness.enums import ReadinessSource
from app.domain.readiness.events import (
    ReadinessRecorded,
    RecoveryMetricsUpdated,
    RecoveryNotesUpdated,
    SleepUpdated,
)
from app.domain.readiness.identifiers import ReadinessId
from app.domain.readiness.readiness import Readiness
from app.domain.readiness.value_objects import (
    EnergyLevel,
    HeartRateVariability,
    ReadinessDate,
    RecoveryNotes,
    RestingHeartRate,
    SleepDuration,
    SleepQuality,
    SorenessLevel,
    StressLevel,
)
from app.domain.shared_kernel.errors import DomainInvariantViolationError
from app.domain.user.identifiers import UserId
from tests.domain.readiness.factories import a_fixed_clock, a_recorded_readiness

# --- record() ---


@pytest.mark.unit
def test_record_exposes_the_required_fields_it_was_given() -> None:
    readiness_id = ReadinessId.generate()
    user_id = UserId.generate()
    readiness = Readiness.record(
        readiness_id=readiness_id,
        user_id=user_id,
        readiness_date=ReadinessDate(date(2026, 1, 1)),
        clock=a_fixed_clock(),
    )
    assert readiness.id == readiness_id
    assert readiness.user_id == user_id
    assert readiness.readiness_date == ReadinessDate(date(2026, 1, 1))


@pytest.mark.unit
def test_record_stamps_recorded_at_from_the_clock() -> None:
    clock = a_fixed_clock()
    readiness = Readiness.record(
        readiness_id=ReadinessId.generate(),
        user_id=UserId.generate(),
        readiness_date=ReadinessDate(date(2026, 1, 1)),
        clock=clock,
    )
    assert readiness.recorded_at == clock.now()


@pytest.mark.unit
def test_record_defaults_every_optional_field_to_none_and_notes_to_empty() -> None:
    readiness = a_recorded_readiness()
    assert readiness.source is None
    assert readiness.sleep_duration is None
    assert readiness.sleep_quality is None
    assert readiness.energy_level is None
    assert readiness.stress_level is None
    assert readiness.soreness_level is None
    assert readiness.resting_heart_rate is None
    assert readiness.heart_rate_variability is None
    assert readiness.notes == RecoveryNotes()
    assert readiness.updated_at is None


@pytest.mark.unit
def test_record_accepts_every_optional_field_at_once() -> None:
    readiness = Readiness.record(
        readiness_id=ReadinessId.generate(),
        user_id=UserId.generate(),
        readiness_date=ReadinessDate(date(2026, 1, 1)),
        clock=a_fixed_clock(),
        source=ReadinessSource.WEARABLE,
        sleep_duration=SleepDuration(timedelta(hours=7)),
        sleep_quality=SleepQuality(8),
        energy_level=EnergyLevel(7),
        stress_level=StressLevel(3),
        soreness_level=SorenessLevel(2),
        resting_heart_rate=RestingHeartRate(58.0),
        heart_rate_variability=HeartRateVariability(65.0),
        notes=RecoveryNotes("Felt great."),
    )
    assert readiness.source == ReadinessSource.WEARABLE
    assert readiness.sleep_duration == SleepDuration(timedelta(hours=7))
    assert readiness.sleep_quality == SleepQuality(8)
    assert readiness.energy_level == EnergyLevel(7)
    assert readiness.stress_level == StressLevel(3)
    assert readiness.soreness_level == SorenessLevel(2)
    assert readiness.resting_heart_rate == RestingHeartRate(58.0)
    assert readiness.heart_rate_variability == HeartRateVariability(65.0)
    assert readiness.notes == RecoveryNotes("Felt great.")


@pytest.mark.unit
def test_record_raises_a_readiness_recorded_event() -> None:
    readiness_id = ReadinessId.generate()
    user_id = UserId.generate()
    readiness_date = ReadinessDate(date(2026, 1, 1))
    clock = a_fixed_clock()

    readiness = Readiness.record(
        readiness_id=readiness_id,
        user_id=user_id,
        readiness_date=readiness_date,
        clock=clock,
        source=ReadinessSource.MANUAL,
    )

    events = readiness.pull_domain_events()
    assert len(events) == 1
    assert isinstance(events[0], ReadinessRecorded)
    assert events[0].readiness_id == readiness_id
    assert events[0].user_id == user_id
    assert events[0].readiness_date == readiness_date
    assert events[0].source == ReadinessSource.MANUAL
    assert events[0].occurred_at == clock.now()


@pytest.mark.unit
def test_record_raises_exactly_one_event_even_with_optional_fields_supplied() -> None:
    readiness = Readiness.record(
        readiness_id=ReadinessId.generate(),
        user_id=UserId.generate(),
        readiness_date=ReadinessDate(date(2026, 1, 1)),
        clock=a_fixed_clock(),
        sleep_duration=SleepDuration(timedelta(hours=7)),
        energy_level=EnergyLevel(7),
        notes=RecoveryNotes("hi"),
    )
    events = readiness.pull_domain_events()
    assert len(events) == 1
    assert isinstance(events[0], ReadinessRecorded)


@pytest.mark.unit
def test_record_generates_a_distinct_readiness_each_time() -> None:
    assert a_recorded_readiness().id != a_recorded_readiness().id


# --- update_sleep() ---


@pytest.mark.unit
def test_update_sleep_sets_previously_unset_fields() -> None:
    readiness = a_recorded_readiness()
    readiness.update_sleep(sleep_duration=SleepDuration(timedelta(hours=7)), clock=a_fixed_clock())
    assert readiness.sleep_duration == SleepDuration(timedelta(hours=7))


@pytest.mark.unit
def test_update_sleep_replaces_a_previously_set_field() -> None:
    readiness = a_recorded_readiness()
    clock = a_fixed_clock()
    readiness.update_sleep(sleep_quality=SleepQuality(6), clock=clock)
    readiness.update_sleep(sleep_quality=SleepQuality(8), clock=clock)
    assert readiness.sleep_quality == SleepQuality(8)


@pytest.mark.unit
def test_update_sleep_none_leaves_other_field_unchanged() -> None:
    readiness = a_recorded_readiness()
    clock = a_fixed_clock()
    readiness.update_sleep(
        sleep_duration=SleepDuration(timedelta(hours=7)), sleep_quality=SleepQuality(8), clock=clock
    )
    readiness.update_sleep(sleep_quality=SleepQuality(9), clock=clock)
    assert readiness.sleep_duration == SleepDuration(timedelta(hours=7))
    assert readiness.sleep_quality == SleepQuality(9)


@pytest.mark.unit
def test_update_sleep_stamps_updated_at() -> None:
    readiness = a_recorded_readiness()
    clock = a_fixed_clock()
    readiness.update_sleep(sleep_quality=SleepQuality(8), clock=clock)
    assert readiness.updated_at == clock.now()


@pytest.mark.unit
def test_update_sleep_records_event_with_full_resulting_snapshot() -> None:
    readiness = a_recorded_readiness()
    clock = a_fixed_clock()
    readiness.update_sleep(sleep_duration=SleepDuration(timedelta(hours=7)), clock=clock)
    readiness.pull_domain_events()  # drain ReadinessRecorded

    readiness.update_sleep(sleep_quality=SleepQuality(8), clock=clock)

    events = readiness.pull_domain_events()
    assert len(events) == 1
    assert isinstance(events[0], SleepUpdated)
    assert events[0].sleep_duration == SleepDuration(timedelta(hours=7))
    assert events[0].sleep_quality == SleepQuality(8)


# --- update_recovery_metrics() ---


@pytest.mark.unit
def test_update_recovery_metrics_sets_previously_unset_fields() -> None:
    readiness = a_recorded_readiness()
    readiness.update_recovery_metrics(energy_level=EnergyLevel(7), clock=a_fixed_clock())
    assert readiness.energy_level == EnergyLevel(7)


@pytest.mark.unit
def test_update_recovery_metrics_replaces_a_previously_set_field() -> None:
    readiness = a_recorded_readiness()
    clock = a_fixed_clock()
    readiness.update_recovery_metrics(stress_level=StressLevel(5), clock=clock)
    readiness.update_recovery_metrics(stress_level=StressLevel(3), clock=clock)
    assert readiness.stress_level == StressLevel(3)


@pytest.mark.unit
def test_update_recovery_metrics_none_leaves_other_fields_unchanged() -> None:
    readiness = a_recorded_readiness()
    clock = a_fixed_clock()
    readiness.update_recovery_metrics(
        energy_level=EnergyLevel(7), stress_level=StressLevel(3), clock=clock
    )
    readiness.update_recovery_metrics(soreness_level=SorenessLevel(2), clock=clock)
    assert readiness.energy_level == EnergyLevel(7)
    assert readiness.stress_level == StressLevel(3)
    assert readiness.soreness_level == SorenessLevel(2)


@pytest.mark.unit
def test_update_recovery_metrics_all_five_fields_at_once() -> None:
    readiness = a_recorded_readiness()
    readiness.update_recovery_metrics(
        energy_level=EnergyLevel(7),
        stress_level=StressLevel(3),
        soreness_level=SorenessLevel(2),
        resting_heart_rate=RestingHeartRate(58.0),
        heart_rate_variability=HeartRateVariability(65.0),
        clock=a_fixed_clock(),
    )
    assert readiness.energy_level == EnergyLevel(7)
    assert readiness.stress_level == StressLevel(3)
    assert readiness.soreness_level == SorenessLevel(2)
    assert readiness.resting_heart_rate == RestingHeartRate(58.0)
    assert readiness.heart_rate_variability == HeartRateVariability(65.0)


@pytest.mark.unit
def test_update_recovery_metrics_stamps_updated_at() -> None:
    readiness = a_recorded_readiness()
    clock = a_fixed_clock()
    readiness.update_recovery_metrics(energy_level=EnergyLevel(7), clock=clock)
    assert readiness.updated_at == clock.now()


@pytest.mark.unit
def test_update_recovery_metrics_records_event_with_full_resulting_snapshot() -> None:
    readiness = a_recorded_readiness()
    clock = a_fixed_clock()
    readiness.update_recovery_metrics(energy_level=EnergyLevel(7), clock=clock)
    readiness.pull_domain_events()  # drain ReadinessRecorded

    readiness.update_recovery_metrics(stress_level=StressLevel(3), clock=clock)

    events = readiness.pull_domain_events()
    assert len(events) == 1
    assert isinstance(events[0], RecoveryMetricsUpdated)
    assert events[0].energy_level == EnergyLevel(7)
    assert events[0].stress_level == StressLevel(3)
    assert events[0].soreness_level is None


@pytest.mark.unit
def test_update_recovery_metrics_is_freely_callable_with_no_lifecycle_gate() -> None:
    """Readiness has no status enum — nothing blocks calling update
    methods repeatedly, unlike Workout/Exercise/WorkoutSession's
    terminal-state guards."""
    readiness = a_recorded_readiness()
    clock = a_fixed_clock()
    for value in (5, 7, 9):
        readiness.update_recovery_metrics(energy_level=EnergyLevel(value), clock=clock)
    assert readiness.energy_level == EnergyLevel(9)


# --- update_notes() ---


@pytest.mark.unit
def test_update_notes_replaces_the_notes() -> None:
    readiness = a_recorded_readiness()
    readiness.update_notes(RecoveryNotes("Slept poorly."), clock=a_fixed_clock())
    assert readiness.notes == RecoveryNotes("Slept poorly.")


@pytest.mark.unit
def test_update_notes_accepts_an_explicitly_empty_value() -> None:
    readiness = a_recorded_readiness()
    clock = a_fixed_clock()
    readiness.update_notes(RecoveryNotes("something"), clock=clock)
    readiness.update_notes(RecoveryNotes(""), clock=clock)
    assert readiness.notes == RecoveryNotes("")


@pytest.mark.unit
def test_update_notes_stamps_updated_at() -> None:
    readiness = a_recorded_readiness()
    clock = a_fixed_clock()
    readiness.update_notes(RecoveryNotes("x"), clock=clock)
    assert readiness.updated_at == clock.now()


@pytest.mark.unit
def test_update_notes_records_a_recovery_notes_updated_event() -> None:
    readiness = a_recorded_readiness()
    clock = a_fixed_clock()
    notes = RecoveryNotes("Slept poorly.")

    readiness.update_notes(notes, clock=clock)

    events = readiness.pull_domain_events()
    assert len(events) == 2  # ReadinessRecorded, then RecoveryNotesUpdated
    assert isinstance(events[-1], RecoveryNotesUpdated)
    assert events[-1].notes == notes
    assert events[-1].occurred_at == clock.now()


# --- __init__ construction (repository rehydration path) ---


@pytest.mark.unit
def test_constructor_rejects_a_naive_recorded_at() -> None:
    with pytest.raises(DomainInvariantViolationError, match="timezone-aware"):
        Readiness(
            ReadinessId.generate(),
            user_id=UserId.generate(),
            readiness_date=ReadinessDate(date(2026, 1, 1)),
            recorded_at=datetime(2026, 1, 1),  # deliberately naive
        )


@pytest.mark.unit
def test_constructor_rehydrates_an_existing_entry_with_no_side_effects() -> None:
    """The path a repository uses to reconstruct a Readiness check-in
    already in storage — no event should be raised."""
    readiness = Readiness(
        ReadinessId.generate(),
        user_id=UserId.generate(),
        readiness_date=ReadinessDate(date(2026, 1, 1)),
        recorded_at=datetime.now(timezone.utc),
        energy_level=EnergyLevel(7),
    )
    assert readiness.pull_domain_events() == []
    assert readiness.energy_level == EnergyLevel(7)


@pytest.mark.unit
def test_constructor_accepts_every_explicit_field() -> None:
    now = datetime.now(timezone.utc)
    readiness = Readiness(
        ReadinessId.generate(),
        user_id=UserId.generate(),
        readiness_date=ReadinessDate(date(2026, 1, 1)),
        recorded_at=now,
        source=ReadinessSource.IMPORTED,
        sleep_duration=SleepDuration(timedelta(hours=7)),
        sleep_quality=SleepQuality(8),
        energy_level=EnergyLevel(7),
        stress_level=StressLevel(3),
        soreness_level=SorenessLevel(2),
        resting_heart_rate=RestingHeartRate(58.0),
        heart_rate_variability=HeartRateVariability(65.0),
        notes=RecoveryNotes("Rehydrated."),
        updated_at=now,
    )
    assert readiness.source == ReadinessSource.IMPORTED
    assert readiness.sleep_duration == SleepDuration(timedelta(hours=7))
    assert readiness.sleep_quality == SleepQuality(8)
    assert readiness.energy_level == EnergyLevel(7)
    assert readiness.stress_level == StressLevel(3)
    assert readiness.soreness_level == SorenessLevel(2)
    assert readiness.resting_heart_rate == RestingHeartRate(58.0)
    assert readiness.heart_rate_variability == HeartRateVariability(65.0)
    assert readiness.notes == RecoveryNotes("Rehydrated.")
    assert readiness.updated_at == now
