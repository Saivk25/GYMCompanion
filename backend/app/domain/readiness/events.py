"""Domain events raised by the Readiness aggregate.

Scoped to exactly the four events this increment's task named —
`ReadinessRecorded`, `SleepUpdated`, `RecoveryMetricsUpdated`,
`RecoveryNotesUpdated` — the same "raise only what the aggregate's own
methods actually do" discipline every other aggregate's `events.py`
already follows.

`SleepUpdated` covers `sleep_duration`/`sleep_quality` together;
`RecoveryMetricsUpdated` covers the remaining observed metrics
(`energy_level`/`stress_level`/`soreness_level`/`resting_heart_rate`/
`heart_rate_variability`) — the same two-group split
`app.domain.progress.events` (`BodyCompositionUpdated`/
`MeasurementsUpdated`) and `app.domain.nutrition.events`
(`NutritionUpdated`/`WaterUpdated`) already use. Both `*Updated` events
carry the full resulting value of every field in their group, not just
what changed in one call — the same choice made throughout this sprint:
a downstream reader needs a coherent snapshot, not a diff.
"""

from dataclasses import dataclass

from app.domain.readiness.enums import ReadinessSource
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
from app.domain.shared_kernel.events import DomainEvent
from app.domain.user.identifiers import UserId


@dataclass(frozen=True, kw_only=True)
class ReadinessRecorded(DomainEvent):
    """A new Readiness check-in was created via `Readiness.record(...)`.
    Carries the identifying fields a first subscriber would need without
    re-fetching the aggregate; sleep/recovery-metric values are covered by
    `SleepUpdated`/`RecoveryMetricsUpdated` when set, including when set
    as part of the same `record()` call — see `readiness.py`'s class
    docstring.
    """

    readiness_id: ReadinessId
    user_id: UserId
    readiness_date: ReadinessDate
    source: ReadinessSource | None


@dataclass(frozen=True, kw_only=True)
class SleepUpdated(DomainEvent):
    """`Readiness.update_sleep(...)` changed `sleep_duration` and/or
    `sleep_quality`. Carries the resulting value of both (each still
    `None` if never set), not just the one this call changed.
    """

    readiness_id: ReadinessId
    user_id: UserId
    sleep_duration: SleepDuration | None
    sleep_quality: SleepQuality | None


@dataclass(frozen=True, kw_only=True)
class RecoveryMetricsUpdated(DomainEvent):
    """`Readiness.update_recovery_metrics(...)` changed one or more of
    `energy_level`/`stress_level`/`soreness_level`/`resting_heart_rate`/
    `heart_rate_variability`. Carries the resulting value of all five
    (each still `None` if never set), not just the ones this call
    changed.
    """

    readiness_id: ReadinessId
    user_id: UserId
    energy_level: EnergyLevel | None
    stress_level: StressLevel | None
    soreness_level: SorenessLevel | None
    resting_heart_rate: RestingHeartRate | None
    heart_rate_variability: HeartRateVariability | None


@dataclass(frozen=True, kw_only=True)
class RecoveryNotesUpdated(DomainEvent):
    """`Readiness.update_notes(...)` replaced this check-in's notes.
    Carries the full new `notes`, the same choice
    `app.domain.progress.events.ProgressNotesUpdated` makes.
    """

    readiness_id: ReadinessId
    user_id: UserId
    notes: RecoveryNotes
