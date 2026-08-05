"""Request/response schemas for the Readiness endpoints
(`app/api/routes/v1/readiness.py`). See `goal.py`'s module docstring for
the conventions this file follows (no duplicated range validation;
`None` means whatever the corresponding command already documents it to
mean).

`sleep_duration` is the one field in this module that isn't a bare
primitive wrapper end-to-end: `SleepDuration` wraps a `datetime.
timedelta`, represented over HTTP as a plain number of seconds via
`duration_to_seconds()`/`seconds_to_duration()` (see `common.py`).
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel

from app.api.schemas.common import duration_to_seconds, seconds_to_duration, unwrap, unwrap_optional
from app.application.readiness.commands.record_readiness import RecordReadinessCommand
from app.application.readiness.commands.update_notes import UpdateNotesCommand
from app.application.readiness.commands.update_recovery_metrics import (
    UpdateRecoveryMetricsCommand,
)
from app.application.readiness.commands.update_sleep import UpdateSleepCommand
from app.application.readiness.dto.readiness_dto import ReadinessDTO
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
from app.domain.user.identifiers import UserId


class RecordReadinessRequest(BaseModel):
    """No `user_id` field — see `app.api.schemas.goal.CreateGoalRequest`'s
    identical docstring for why."""

    readiness_date: date
    source: ReadinessSource | None = None
    sleep_duration_seconds: float | None = None
    sleep_quality: int | None = None
    energy_level: int | None = None
    stress_level: int | None = None
    soreness_level: int | None = None
    resting_heart_rate: float | None = None
    heart_rate_variability: float | None = None
    notes: str | None = None

    def to_command(self, user_id: UserId) -> RecordReadinessCommand:
        return RecordReadinessCommand(
            user_id=user_id,
            readiness_date=ReadinessDate(self.readiness_date),
            source=self.source,
            sleep_duration=(
                SleepDuration(seconds_to_duration(self.sleep_duration_seconds))
                if self.sleep_duration_seconds is not None
                else None
            ),
            sleep_quality=(
                SleepQuality(self.sleep_quality) if self.sleep_quality is not None else None
            ),
            energy_level=EnergyLevel(self.energy_level) if self.energy_level is not None else None,
            stress_level=StressLevel(self.stress_level) if self.stress_level is not None else None,
            soreness_level=(
                SorenessLevel(self.soreness_level) if self.soreness_level is not None else None
            ),
            resting_heart_rate=(
                RestingHeartRate(self.resting_heart_rate)
                if self.resting_heart_rate is not None
                else None
            ),
            heart_rate_variability=(
                HeartRateVariability(self.heart_rate_variability)
                if self.heart_rate_variability is not None
                else None
            ),
            notes=RecoveryNotes(self.notes) if self.notes is not None else None,
        )


class UpdateSleepRequest(BaseModel):
    sleep_duration_seconds: float | None = None
    sleep_quality: int | None = None

    def to_command(self, readiness_id: ReadinessId, requester_id: UserId) -> UpdateSleepCommand:
        return UpdateSleepCommand(
            readiness_id=readiness_id,
            requester_id=requester_id,
            sleep_duration=(
                SleepDuration(seconds_to_duration(self.sleep_duration_seconds))
                if self.sleep_duration_seconds is not None
                else None
            ),
            sleep_quality=(
                SleepQuality(self.sleep_quality) if self.sleep_quality is not None else None
            ),
        )


class UpdateRecoveryMetricsRequest(BaseModel):
    energy_level: int | None = None
    stress_level: int | None = None
    soreness_level: int | None = None
    resting_heart_rate: float | None = None
    heart_rate_variability: float | None = None

    def to_command(
        self, readiness_id: ReadinessId, requester_id: UserId
    ) -> UpdateRecoveryMetricsCommand:
        return UpdateRecoveryMetricsCommand(
            readiness_id=readiness_id,
            requester_id=requester_id,
            energy_level=EnergyLevel(self.energy_level) if self.energy_level is not None else None,
            stress_level=StressLevel(self.stress_level) if self.stress_level is not None else None,
            soreness_level=(
                SorenessLevel(self.soreness_level) if self.soreness_level is not None else None
            ),
            resting_heart_rate=(
                RestingHeartRate(self.resting_heart_rate)
                if self.resting_heart_rate is not None
                else None
            ),
            heart_rate_variability=(
                HeartRateVariability(self.heart_rate_variability)
                if self.heart_rate_variability is not None
                else None
            ),
        )


class UpdateReadinessNotesRequest(BaseModel):
    notes: str

    def to_command(self, readiness_id: ReadinessId, requester_id: UserId) -> UpdateNotesCommand:
        return UpdateNotesCommand(
            readiness_id=readiness_id, requester_id=requester_id, notes=RecoveryNotes(self.notes)
        )


class ReadinessResponse(BaseModel):
    readiness_id: str
    user_id: str
    readiness_date: date
    recorded_at: str
    source: ReadinessSource | None
    sleep_duration_seconds: float | None
    sleep_quality: int | None
    energy_level: int | None
    stress_level: int | None
    soreness_level: int | None
    resting_heart_rate: float | None
    heart_rate_variability: float | None
    notes: str
    updated_at: str | None

    @classmethod
    def from_dto(cls, dto: ReadinessDTO) -> ReadinessResponse:
        return cls(
            readiness_id=str(dto.readiness_id),
            user_id=str(dto.user_id),
            readiness_date=unwrap(dto.readiness_date),
            recorded_at=dto.recorded_at.isoformat(),
            source=dto.source,
            sleep_duration_seconds=(
                duration_to_seconds(dto.sleep_duration.value)
                if dto.sleep_duration is not None
                else None
            ),
            sleep_quality=unwrap_optional(dto.sleep_quality),
            energy_level=unwrap_optional(dto.energy_level),
            stress_level=unwrap_optional(dto.stress_level),
            soreness_level=unwrap_optional(dto.soreness_level),
            resting_heart_rate=unwrap_optional(dto.resting_heart_rate),
            heart_rate_variability=unwrap_optional(dto.heart_rate_variability),
            notes=unwrap(dto.notes),
            updated_at=dto.updated_at.isoformat() if dto.updated_at is not None else None,
        )
