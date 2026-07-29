"""`ProgressContext`: a read-only snapshot of a Progress record for domain
services.

Same purpose as `UserContext`, `WorkoutContext`, `ExerciseContext`, and
`WorkoutSessionContext`: lets a future domain service — Progress
Intelligence's trend/plateau/forecast computation, none built yet — consume
everything it needs to know about one check-in in a single immutable
value.
"""

from __future__ import annotations

from dataclasses import dataclass
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
from app.domain.shared_kernel.value_object import ValueObject
from app.domain.user.identifiers import UserId

if TYPE_CHECKING:
    # Import only for the type checker — see UserContext's identical note
    # for why this avoids a real circular import at module load time.
    from app.domain.progress.progress import Progress


@dataclass(frozen=True, kw_only=True)
class ProgressContext(ValueObject):
    """An immutable snapshot of one Progress record, taken at a point in
    time."""

    progress_id: ProgressId
    user_id: UserId
    progress_date: ProgressDate
    unit: MeasurementUnit
    source: ProgressSource
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

    @classmethod
    def from_progress(cls, progress: Progress) -> ProgressContext:
        """Builds a snapshot from a live `Progress` aggregate. One-
        directional on purpose: `Progress` does not know this type exists.
        """
        return cls(
            progress_id=progress.id,
            user_id=progress.user_id,
            progress_date=progress.progress_date,
            unit=progress.unit,
            source=progress.source,
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
        )
