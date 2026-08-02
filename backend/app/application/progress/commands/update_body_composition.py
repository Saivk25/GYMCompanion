"""`UpdateBodyCompositionCommand`: the input to
`UpdateBodyCompositionHandler`.

Mirrors `Progress.update_body_composition()`'s own "`None` means leave
unchanged" convention exactly — the same "carry the aggregate method's
own semantics through unmodified" reasoning
`docs/adr/0025-nutrition-application-use-cases.md` documents for
`UpdateNutritionCommand`. Not the opposite ("`None` means clear")
convention `UpdateWorkoutCommand` uses for `Workout`'s `goal`/`notes` —
this command mirrors whichever convention the aggregate method it
invokes already defines, never inventing one of its own.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.application.shared.command import Command
from app.domain.progress.identifiers import ProgressId
from app.domain.progress.value_objects import (
    BodyFatPercentage,
    BodyWeight,
    LeanBodyMass,
    MuscleMass,
)


@dataclass(frozen=True, kw_only=True)
class UpdateBodyCompositionCommand(Command):
    """Replace whichever body-composition fields are given on an
    existing Progress record; fields left as `None` are left unchanged."""

    progress_id: ProgressId
    body_weight: BodyWeight | None = None
    body_fat_percentage: BodyFatPercentage | None = None
    lean_body_mass: LeanBodyMass | None = None
    muscle_mass: MuscleMass | None = None
