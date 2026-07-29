"""The Readiness aggregate root.

The canonical record of a user's daily recovery inputs: sleep, subjective
energy/stress/soreness, resting heart rate, and heart rate variability.
Domain Model & Decision Engine Bible, Section 4.8's `ReadinessCheckIn`
("today's snapshot", Table 11) is the closest analog. This increment
stores observations only — it does not compute a readiness score, a
recovery band, deload triggers, or anything derived from a window of
check-ins; that is `RecoveryState`'s job (Table 11's sibling entity, "the
rolling, derived state built from a window of check-ins plus training
load"), a separate, not-yet-built concept that reads this aggregate's
events, never the other way around. Future rule engines consume these
records; none are implemented here.

Two of this increment's value objects — `RestingHeartRate` and
`HeartRateVariability` — are not in the Bible's own `ReadinessCheckIn`
attribute list (`checkin_id, date, sleep_hours, stress_level, soreness,
pain_flags, GI_symptoms, time_available`); they're this increment's own
addition, the common wearable-derived metrics a `ReadinessSource.WEARABLE`
entry would actually carry. `pain_flags`/`GI_symptoms` are deliberately
not modeled here — the Bible routes those through `SafetyFlag`
(Section 4, Table 2's Recovery & Safety context), a separate aggregate
this increment doesn't build.

The Bible states "One CheckIn per day" as a validation rule (Table 11).
This aggregate does not enforce that itself — a single `Readiness`
instance has no visibility into any other instance for the same user/date,
the same reason no aggregate in this codebase enforces a uniqueness
constraint against sibling records (e.g. `User`'s unique email) at the
domain layer. Enforcing "one per day" is an application/repository-layer
concern for whichever increment adds a real persistence implementation.

Tenant-scoped like every other per-user aggregate in this codebase
(carries `user_id`). No status enum and no lifecycle — a check-in is a
fact captured at a point in time, the same shape `app.domain.progress.
progress.Progress` and `app.domain.nutrition.nutrition.Nutrition` already
use. `source` is optional, following the same "don't require what the
task's Rules list doesn't explicitly require" discipline
`docs/adr/0011-nutrition-is-a-per-entry-log-not-a-daily-rollup.md`
documents for `Nutrition.source`/`meal_type`.
"""

from __future__ import annotations

from datetime import datetime

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
from app.domain.shared_kernel.aggregate_root import AggregateRoot
from app.domain.shared_kernel.clock import Clock
from app.domain.shared_kernel.validation import ensure
from app.domain.user.identifiers import UserId


class Readiness(AggregateRoot[ReadinessId]):
    """The Readiness aggregate. See the module docstring for scope.

    Construct a brand-new check-in via the `record()` factory, never
    `Readiness(...)` directly — the constructor is also used to rehydrate
    an existing check-in from a repository, where re-raising
    `ReadinessRecorded` would be wrong.
    """

    def __init__(
        self,
        readiness_id: ReadinessId,
        *,
        user_id: UserId,
        readiness_date: ReadinessDate,
        recorded_at: datetime,
        source: ReadinessSource | None = None,
        sleep_duration: SleepDuration | None = None,
        sleep_quality: SleepQuality | None = None,
        energy_level: EnergyLevel | None = None,
        stress_level: StressLevel | None = None,
        soreness_level: SorenessLevel | None = None,
        resting_heart_rate: RestingHeartRate | None = None,
        heart_rate_variability: HeartRateVariability | None = None,
        notes: RecoveryNotes | None = None,
        updated_at: datetime | None = None,
    ) -> None:
        super().__init__(readiness_id)
        ensure(recorded_at.tzinfo is not None, "recorded_at must be timezone-aware")
        self._user_id = user_id
        self._readiness_date = readiness_date
        self._recorded_at = recorded_at
        self._source = source
        self._sleep_duration = sleep_duration
        self._sleep_quality = sleep_quality
        self._energy_level = energy_level
        self._stress_level = stress_level
        self._soreness_level = soreness_level
        self._resting_heart_rate = resting_heart_rate
        self._heart_rate_variability = heart_rate_variability
        self._notes = notes if notes is not None else RecoveryNotes()
        self._updated_at = updated_at

    @classmethod
    def record(
        cls,
        *,
        readiness_id: ReadinessId,
        user_id: UserId,
        readiness_date: ReadinessDate,
        clock: Clock,
        source: ReadinessSource | None = None,
        sleep_duration: SleepDuration | None = None,
        sleep_quality: SleepQuality | None = None,
        energy_level: EnergyLevel | None = None,
        stress_level: StressLevel | None = None,
        soreness_level: SorenessLevel | None = None,
        resting_heart_rate: RestingHeartRate | None = None,
        heart_rate_variability: HeartRateVariability | None = None,
        notes: RecoveryNotes | None = None,
    ) -> Readiness:
        """Creates a brand-new Readiness check-in and records
        `ReadinessRecorded`. `readiness_id` is generated by the caller
        (`ReadinessId.generate()`) before calling this — the same
        convention every other aggregate's factory follows.

        Every sleep/recovery-metric field can be supplied here directly
        (the common case: a single check-in where everything was captured
        at once, e.g. synced from a wearable) or filled in afterward via
        `update_sleep()`/`update_recovery_metrics()` — both are equally
        valid.
        """
        recorded_at = clock.now()
        readiness = cls(
            readiness_id,
            user_id=user_id,
            readiness_date=readiness_date,
            recorded_at=recorded_at,
            source=source,
            sleep_duration=sleep_duration,
            sleep_quality=sleep_quality,
            energy_level=energy_level,
            stress_level=stress_level,
            soreness_level=soreness_level,
            resting_heart_rate=resting_heart_rate,
            heart_rate_variability=heart_rate_variability,
            notes=notes,
        )
        readiness.record_event(
            ReadinessRecorded(
                occurred_at=recorded_at,
                readiness_id=readiness_id,
                user_id=user_id,
                readiness_date=readiness_date,
                source=source,
            )
        )
        return readiness

    @property
    def user_id(self) -> UserId:
        return self._user_id

    @property
    def readiness_date(self) -> ReadinessDate:
        return self._readiness_date

    @property
    def recorded_at(self) -> datetime:
        return self._recorded_at

    @property
    def source(self) -> ReadinessSource | None:
        return self._source

    @property
    def sleep_duration(self) -> SleepDuration | None:
        return self._sleep_duration

    @property
    def sleep_quality(self) -> SleepQuality | None:
        return self._sleep_quality

    @property
    def energy_level(self) -> EnergyLevel | None:
        return self._energy_level

    @property
    def stress_level(self) -> StressLevel | None:
        return self._stress_level

    @property
    def soreness_level(self) -> SorenessLevel | None:
        return self._soreness_level

    @property
    def resting_heart_rate(self) -> RestingHeartRate | None:
        return self._resting_heart_rate

    @property
    def heart_rate_variability(self) -> HeartRateVariability | None:
        return self._heart_rate_variability

    @property
    def notes(self) -> RecoveryNotes:
        return self._notes

    @property
    def updated_at(self) -> datetime | None:
        return self._updated_at

    def update_sleep(
        self,
        *,
        clock: Clock,
        sleep_duration: SleepDuration | None = None,
        sleep_quality: SleepQuality | None = None,
    ) -> None:
        """Replaces whichever sleep fields are given (`None` means "leave
        unchanged", the same convention
        `app.domain.progress.progress.Progress.update_body_composition()`
        uses) and records one `SleepUpdated` carrying the resulting value
        of both fields.
        """
        if sleep_duration is not None:
            self._sleep_duration = sleep_duration
        if sleep_quality is not None:
            self._sleep_quality = sleep_quality
        self._updated_at = clock.now()
        self.record_event(
            SleepUpdated(
                occurred_at=self._updated_at,
                readiness_id=self.id,
                user_id=self._user_id,
                sleep_duration=self._sleep_duration,
                sleep_quality=self._sleep_quality,
            )
        )

    def update_recovery_metrics(
        self,
        *,
        clock: Clock,
        energy_level: EnergyLevel | None = None,
        stress_level: StressLevel | None = None,
        soreness_level: SorenessLevel | None = None,
        resting_heart_rate: RestingHeartRate | None = None,
        heart_rate_variability: HeartRateVariability | None = None,
    ) -> None:
        """Replaces whichever recovery-metric fields are given (`None`
        means "leave unchanged") and records one `RecoveryMetricsUpdated`
        carrying the resulting value of all five fields.
        """
        if energy_level is not None:
            self._energy_level = energy_level
        if stress_level is not None:
            self._stress_level = stress_level
        if soreness_level is not None:
            self._soreness_level = soreness_level
        if resting_heart_rate is not None:
            self._resting_heart_rate = resting_heart_rate
        if heart_rate_variability is not None:
            self._heart_rate_variability = heart_rate_variability
        self._updated_at = clock.now()
        self.record_event(
            RecoveryMetricsUpdated(
                occurred_at=self._updated_at,
                readiness_id=self.id,
                user_id=self._user_id,
                energy_level=self._energy_level,
                stress_level=self._stress_level,
                soreness_level=self._soreness_level,
                resting_heart_rate=self._resting_heart_rate,
                heart_rate_variability=self._heart_rate_variability,
            )
        )

    def update_notes(self, notes: RecoveryNotes, *, clock: Clock) -> None:
        """Replaces this check-in's notes wholesale and records one
        `RecoveryNotesUpdated`."""
        self._notes = notes
        self._updated_at = clock.now()
        self.record_event(
            RecoveryNotesUpdated(
                occurred_at=self._updated_at,
                readiness_id=self.id,
                user_id=self._user_id,
                notes=notes,
            )
        )
