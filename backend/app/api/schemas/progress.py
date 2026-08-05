"""Request/response schemas for the Progress endpoints
(`app/api/routes/v1/progress.py`). See `goal.py`'s module docstring for
the conventions this file follows (no duplicated range validation;
`None` means whatever the corresponding command already documents it to
mean).
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel

from app.api.schemas.common import unwrap, unwrap_optional
from app.application.progress.commands.record_progress import RecordProgressCommand
from app.application.progress.commands.update_body_composition import (
    UpdateBodyCompositionCommand,
)
from app.application.progress.commands.update_measurements import UpdateMeasurementsCommand
from app.application.progress.commands.update_notes import UpdateNotesCommand
from app.application.progress.dto.progress_dto import ProgressDTO
from app.domain.progress.enums import MeasurementUnit, ProgressSource
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


class RecordProgressRequest(BaseModel):
    """No `user_id` field — see `app.api.schemas.goal.CreateGoalRequest`'s
    identical docstring for why."""

    progress_date: date
    unit: MeasurementUnit
    source: ProgressSource
    body_weight: float | None = None
    body_fat_percentage: float | None = None
    lean_body_mass: float | None = None
    muscle_mass: float | None = None
    waist: float | None = None
    chest: float | None = None
    hip: float | None = None
    arm: float | None = None
    thigh: float | None = None
    calf: float | None = None
    neck: float | None = None
    notes: str | None = None

    def to_command(self, user_id: UserId) -> RecordProgressCommand:
        return RecordProgressCommand(
            user_id=user_id,
            progress_date=ProgressDate(self.progress_date),
            unit=self.unit,
            source=self.source,
            body_weight=BodyWeight(self.body_weight) if self.body_weight is not None else None,
            body_fat_percentage=(
                BodyFatPercentage(self.body_fat_percentage)
                if self.body_fat_percentage is not None
                else None
            ),
            lean_body_mass=(
                LeanBodyMass(self.lean_body_mass) if self.lean_body_mass is not None else None
            ),
            muscle_mass=MuscleMass(self.muscle_mass) if self.muscle_mass is not None else None,
            waist=WaistMeasurement(self.waist) if self.waist is not None else None,
            chest=ChestMeasurement(self.chest) if self.chest is not None else None,
            hip=HipMeasurement(self.hip) if self.hip is not None else None,
            arm=ArmMeasurement(self.arm) if self.arm is not None else None,
            thigh=ThighMeasurement(self.thigh) if self.thigh is not None else None,
            calf=CalfMeasurement(self.calf) if self.calf is not None else None,
            neck=NeckMeasurement(self.neck) if self.neck is not None else None,
            notes=ProgressNotes(self.notes) if self.notes is not None else None,
        )


class UpdateBodyCompositionRequest(BaseModel):
    body_weight: float | None = None
    body_fat_percentage: float | None = None
    lean_body_mass: float | None = None
    muscle_mass: float | None = None

    def to_command(
        self, progress_id: ProgressId, requester_id: UserId
    ) -> UpdateBodyCompositionCommand:
        return UpdateBodyCompositionCommand(
            progress_id=progress_id,
            requester_id=requester_id,
            body_weight=BodyWeight(self.body_weight) if self.body_weight is not None else None,
            body_fat_percentage=(
                BodyFatPercentage(self.body_fat_percentage)
                if self.body_fat_percentage is not None
                else None
            ),
            lean_body_mass=(
                LeanBodyMass(self.lean_body_mass) if self.lean_body_mass is not None else None
            ),
            muscle_mass=MuscleMass(self.muscle_mass) if self.muscle_mass is not None else None,
        )


class UpdateMeasurementsRequest(BaseModel):
    waist: float | None = None
    chest: float | None = None
    hip: float | None = None
    arm: float | None = None
    thigh: float | None = None
    calf: float | None = None
    neck: float | None = None

    def to_command(
        self, progress_id: ProgressId, requester_id: UserId
    ) -> UpdateMeasurementsCommand:
        return UpdateMeasurementsCommand(
            progress_id=progress_id,
            requester_id=requester_id,
            waist=WaistMeasurement(self.waist) if self.waist is not None else None,
            chest=ChestMeasurement(self.chest) if self.chest is not None else None,
            hip=HipMeasurement(self.hip) if self.hip is not None else None,
            arm=ArmMeasurement(self.arm) if self.arm is not None else None,
            thigh=ThighMeasurement(self.thigh) if self.thigh is not None else None,
            calf=CalfMeasurement(self.calf) if self.calf is not None else None,
            neck=NeckMeasurement(self.neck) if self.neck is not None else None,
        )


class UpdateProgressNotesRequest(BaseModel):
    notes: str

    def to_command(self, progress_id: ProgressId, requester_id: UserId) -> UpdateNotesCommand:
        return UpdateNotesCommand(
            progress_id=progress_id, requester_id=requester_id, notes=ProgressNotes(self.notes)
        )


class ProgressResponse(BaseModel):
    progress_id: str
    user_id: str
    progress_date: date
    unit: MeasurementUnit
    source: ProgressSource
    recorded_at: str
    body_weight: float | None
    body_fat_percentage: float | None
    lean_body_mass: float | None
    muscle_mass: float | None
    waist: float | None
    chest: float | None
    hip: float | None
    arm: float | None
    thigh: float | None
    calf: float | None
    neck: float | None
    notes: str
    updated_at: str | None

    @classmethod
    def from_dto(cls, dto: ProgressDTO) -> ProgressResponse:
        return cls(
            progress_id=str(dto.progress_id),
            user_id=str(dto.user_id),
            progress_date=unwrap(dto.progress_date),
            unit=dto.unit,
            source=dto.source,
            recorded_at=dto.recorded_at.isoformat(),
            body_weight=unwrap_optional(dto.body_weight),
            body_fat_percentage=unwrap_optional(dto.body_fat_percentage),
            lean_body_mass=unwrap_optional(dto.lean_body_mass),
            muscle_mass=unwrap_optional(dto.muscle_mass),
            waist=unwrap_optional(dto.waist),
            chest=unwrap_optional(dto.chest),
            hip=unwrap_optional(dto.hip),
            arm=unwrap_optional(dto.arm),
            thigh=unwrap_optional(dto.thigh),
            calf=unwrap_optional(dto.calf),
            neck=unwrap_optional(dto.neck),
            notes=unwrap(dto.notes),
            updated_at=dto.updated_at.isoformat() if dto.updated_at is not None else None,
        )
