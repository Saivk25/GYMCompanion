"""`UpdateWaterCommand`: the input to `UpdateWaterHandler`.

A separate command from `UpdateNutritionCommand`, matching
`Nutrition.update_water()` being its own aggregate method distinct from
`update_nutrition()` — see `value_objects.py`'s `WaterIntake` docstring
for why water is tracked apart from the other macro fields. Unlike
`UpdateNutritionCommand`'s fields, `water_intake` here is required:
`Nutrition.update_water(water_intake: WaterIntake, ...)` takes no
optional/"leave unchanged" form, so neither does this command.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.application.shared.command import Command
from app.domain.nutrition.identifiers import NutritionId
from app.domain.nutrition.value_objects import WaterIntake
from app.domain.user.identifiers import UserId


@dataclass(frozen=True, kw_only=True)
class UpdateWaterCommand(Command):
    """Replace an existing Nutrition entry's water intake wholesale.

    `requester_id` is the authenticated caller — see
    `app.application.nutrition.queries.get_nutrition.GetNutritionQuery`'s
    own module docstring for the full ownership-check reasoning, which
    applies identically here.
    """

    nutrition_id: NutritionId
    requester_id: UserId
    water_intake: WaterIntake
