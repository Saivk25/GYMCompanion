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
from app.domain.user.identifiers import UserId


@dataclass(frozen=True, kw_only=True)
class UpdateMeasurementsCommand(Command):
    """Replace whichever tape measurements are given on an existing
    Progress record; fields left as `None` are left unchanged.

    `requester_id` is the authenticated caller — see
    `app.application.progress.queries.get_progress.GetProgressQuery`'s
    own module docstring for the full ownership-check reasoning, which
    applies identically here.
    """

    progress_id: ProgressId
    requester_id: UserId
    waist: WaistMeasurement | None = None
    chest: ChestMeasurement | None = None
    hip: HipMeasurement | None = None
    arm: ArmMeasurement | None = None
    thigh: ThighMeasurement | None = None
    calf: CalfMeasurement | None = None
    neck: NeckMeasurement | None = None
