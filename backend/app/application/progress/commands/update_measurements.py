"""`UpdateMeasurementsCommand`: the input to `UpdateMeasurementsHandler`.

Mirrors `Progress.update_measurements()`'s own "`None` means leave
unchanged" convention exactly — see `UpdateBodyCompositionCommand`'s
module docstring for the same reasoning applied to the tape-measurement
field group instead of body composition.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.application.shared.command import Command
from app.domain.progress.identifiers import ProgressId
from app.domain.progress.value_objects import (
    ArmMeasurement,
    CalfMeasurement,
    ChestMeasurement,
    HipMeasurement,
    NeckMeasurement,
    ThighMeasurement,
    WaistMeasurement,
)


@dataclass(frozen=True, kw_only=True)
class UpdateMeasurementsCommand(Command):
    """Replace whichever tape measurements are given on an existing
    Progress record; fields left as `None` are left unchanged."""

    progress_id: ProgressId
    waist: WaistMeasurement | None = None
    chest: ChestMeasurement | None = None
    hip: HipMeasurement | None = None
    arm: ArmMeasurement | None = None
    thigh: ThighMeasurement | None = None
    calf: CalfMeasurement | None = None
    neck: NeckMeasurement | None = None
