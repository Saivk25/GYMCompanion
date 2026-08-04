"""`RecordReadinessCommand`: the input to `RecordReadinessHandler`.

Mirrors `Readiness.record(...)`'s own keyword shape exactly: every
sleep/recovery-metric field is optional, matching the aggregate's own
"everything can be supplied now or filled in afterward" design
(`readiness.py`'s class docstring). Carries `user_id` because, unlike
`UpdateSleepCommand`/`UpdateRecoveryMetricsCommand`/`UpdateNotesCommand`/
`DeleteReadinessCommand` (which target an existing check-in by
`ReadinessId`), this command creates a brand-new check-in with no id
yet — the same "creation command carries the owner id, mutation
commands carry the aggregate id" split every prior phase's `Record`/
`Create` command already establishes.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.application.shared.command import Command
from app.domain.readiness.enums import ReadinessSource
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


@dataclass(frozen=True, kw_only=True)
class RecordReadinessCommand(Command):
    """Record a brand-new Readiness check-in for a User."""

    user_id: UserId
    readiness_date: ReadinessDate
    source: ReadinessSource | None = None
    sleep_duration: SleepDuration | None = None
    sleep_quality: SleepQuality | None = None
    energy_level: EnergyLevel | None = None
    stress_level: StressLevel | None = None
    soreness_level: SorenessLevel | None = None
    resting_heart_rate: RestingHeartRate | None = None
    heart_rate_variability: HeartRateVariability | None = None
    notes: RecoveryNotes | None = None
