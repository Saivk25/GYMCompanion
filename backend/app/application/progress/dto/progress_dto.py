"""`ProgressDTO`: the read-only projection of a `Progress` aggregate
returned to whatever calls a Progress query handler.

Not the same type as `app.domain.progress.context.ProgressContext` —
identical reasoning to `NutritionDTO`'s own module docstring
(`app.application.nutrition.dto.nutrition_dto`): `ProgressContext` is
scoped to `ProgressEvaluationRuleEngine` (and any future Progress
Intelligence trend/plateau/forecast computation, not built yet),
one-directional, and never crosses the Application Layer boundary;
`ProgressDTO` is this layer's own read projection for
`GetProgressHandler`/`ListProgressHandler`, a different consumer with
different reasons to change independently. See `docs/adr/0026-progress-
application-use-cases.md`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

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

if TYPE_CHECKING:
    # Import only for the type checker — see UserDTO's identical note
    # for why this avoids a real circular import at module load time.
    from app.domain.progress.progress import Progress


@dataclass(frozen=True, kw_only=True)
class ProgressDTO:
    """An immutable, read-only snapshot of one `Progress` record, taken
    at query time."""

    progress_id: ProgressId
    user_id: UserId
    progress_date: ProgressDate
    unit: MeasurementUnit
    source: ProgressSource
    recorded_at: datetime
    body_weight: BodyWeight | None
    body_fat_percentage: BodyFatPercentage | None
    lean_body_mass: LeanBodyMass | None
    muscle_mass: MuscleMass | None
    waist: WaistMeasurement | None
    chest: ChestMeasurement | None
    hip: HipMeasurement | None
    arm: ArmMeasurement | None
    thigh: ThighMeasurement | None
    calf: CalfMeasurement | None
    neck: NeckMeasurement | None
    notes: ProgressNotes
    updated_at: datetime | None

    @classmethod
    def from_progress(cls, progress: Progress) -> ProgressDTO:
        """Builds a DTO from a live `Progress` aggregate. One-
        directional on purpose, mirroring `NutritionDTO.from_nutrition` —
        `Progress` never depends on this type.
        """
        return cls(
            progress_id=progress.id,
            user_id=progress.user_id,
            progress_date=progress.progress_date,
            unit=progress.unit,
            source=progress.source,
            recorded_at=progress.recorded_at,
            body_weight=progress.body_weight,
            body_fat_percentage=progress.body_fat_percentage,
            lean_body_mass=progress.lean_body_mass,
            muscle_mass=progress.muscle_mass,
            waist=progress.waist,
            chest=progress.chest,
            hip=progress.hip,
            arm=progress.arm,
            thigh=progress.thigh,
            calf=progress.calf,
            neck=progress.neck,
            notes=progress.notes,
            updated_at=progress.updated_at,
        )
