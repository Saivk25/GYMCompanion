"""`RecordProgressCommand`: the input to `RecordProgressHandler`.

Mirrors `Progress.record(...)`'s own parameter list — every body-
composition/measurement field is optional, matching the aggregate
factory's own "supply everything at once, or fill it in later via
`update_body_composition()`/`update_measurements()`" flexibility (see
`progress.py`'s class docstring). `unit`/`source` are required, matching
`Progress.record(...)` requiring them (no default on the aggregate
side).
"""

from __future__ import annotations

from dataclasses import dataclass

from app.application.shared.command import Command
from app.domain.progress.enums import MeasurementUnit, ProgressSource
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


@dataclass(frozen=True, kw_only=True)
class RecordProgressCommand(Command):
    """Record a brand-new Progress check-in for an existing User."""

    user_id: UserId
    progress_date: ProgressDate
    unit: MeasurementUnit
    source: ProgressSource
    body_weight: BodyWeight | None = None
    body_fat_percentage: BodyFatPercentage | None = None
    lean_body_mass: LeanBodyMass | None = None
    muscle_mass: MuscleMass | None = None
    waist: WaistMeasurement | None = None
    chest: ChestMeasurement | None = None
    hip: HipMeasurement | None = None
    arm: ArmMeasurement | None = None
    thigh: ThighMeasurement | None = None
    calf: CalfMeasurement | None = None
    neck: NeckMeasurement | None = None
    notes: ProgressNotes | None = None
