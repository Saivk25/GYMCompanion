"""Tests for app/domain/readiness/events.py.

Immutability, `event_id` auto-generation, and `occurred_at` timezone
enforcement are `DomainEvent` base behavior, already fully covered by
`tests/domain/shared_kernel/test_events.py`. This file only proves each
Readiness-specific event carries the fields it's supposed to.
"""

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
from app.domain.user.identifiers import UserId


@pytest.mark.unit
def test_readiness_recorded_carries_identifying_fields() -> None:
    readiness_id = ReadinessId.generate()
    user_id = UserId.generate()
    readiness_date = ReadinessDate(date(2026, 1, 1))
    event = ReadinessRecorded(
        occurred_at=datetime.now(timezone.utc),
        readiness_id=readiness_id,
        user_id=user_id,
        readiness_date=readiness_date,
        source=ReadinessSource.WEARABLE,
    )
    assert event.readiness_id == readiness_id
    assert event.user_id == user_id
    assert event.readiness_date == readiness_date
    assert event.source == ReadinessSource.WEARABLE


@pytest.mark.unit
def test_readiness_recorded_allows_source_to_be_none() -> None:
    event = ReadinessRecorded(
        occurred_at=datetime.now(timezone.utc),
        readiness_id=ReadinessId.generate(),
        user_id=UserId.generate(),
        readiness_date=ReadinessDate(date(2026, 1, 1)),
        source=None,
    )
    assert event.source is None


@pytest.mark.unit
def test_sleep_updated_carries_both_fields() -> None:
    readiness_id = ReadinessId.generate()
    sleep_duration = SleepDuration(timedelta(hours=7))
    sleep_quality = SleepQuality(8)
    event = SleepUpdated(
        occurred_at=datetime.now(timezone.utc),
        readiness_id=readiness_id,
        user_id=UserId.generate(),
        sleep_duration=sleep_duration,
        sleep_quality=sleep_quality,
    )
    assert event.readiness_id == readiness_id
    assert event.sleep_duration == sleep_duration
    assert event.sleep_quality == sleep_quality


@pytest.mark.unit
def test_sleep_updated_allows_either_field_to_be_none() -> None:
    event = SleepUpdated(
        occurred_at=datetime.now(timezone.utc),
        readiness_id=ReadinessId.generate(),
        user_id=UserId.generate(),
        sleep_duration=None,
        sleep_quality=None,
    )
    assert event.sleep_duration is None
    assert event.sleep_quality is None


@pytest.mark.unit
def test_recovery_metrics_updated_carries_all_five_fields() -> None:
    readiness_id = ReadinessId.generate()
    energy_level = EnergyLevel(7)
    stress_level = StressLevel(4)
    soreness_level = SorenessLevel(3)
    resting_heart_rate = RestingHeartRate(58.0)
    heart_rate_variability = HeartRateVariability(65.0)
    event = RecoveryMetricsUpdated(
        occurred_at=datetime.now(timezone.utc),
        readiness_id=readiness_id,
        user_id=UserId.generate(),
        energy_level=energy_level,
        stress_level=stress_level,
        soreness_level=soreness_level,
        resting_heart_rate=resting_heart_rate,
        heart_rate_variability=heart_rate_variability,
    )
    assert event.readiness_id == readiness_id
    assert event.energy_level == energy_level
    assert event.stress_level == stress_level
    assert event.soreness_level == soreness_level
    assert event.resting_heart_rate == resting_heart_rate
    assert event.heart_rate_variability == heart_rate_variability


@pytest.mark.unit
def test_recovery_metrics_updated_allows_any_field_to_be_none() -> None:
    event = RecoveryMetricsUpdated(
        occurred_at=datetime.now(timezone.utc),
        readiness_id=ReadinessId.generate(),
        user_id=UserId.generate(),
        energy_level=None,
        stress_level=None,
        soreness_level=None,
        resting_heart_rate=None,
        heart_rate_variability=None,
    )
    assert event.energy_level is None
    assert event.heart_rate_variability is None


@pytest.mark.unit
def test_recovery_notes_updated_carries_the_full_new_notes() -> None:
    readiness_id = ReadinessId.generate()
    notes = RecoveryNotes("Slept poorly.")
    event = RecoveryNotesUpdated(
        occurred_at=datetime.now(timezone.utc),
        readiness_id=readiness_id,
        user_id=UserId.generate(),
        notes=notes,
    )
    assert event.readiness_id == readiness_id
    assert event.notes == notes
