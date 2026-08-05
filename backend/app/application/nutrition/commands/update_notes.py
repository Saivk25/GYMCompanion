"""`UpdateNutritionNotesCommand`: the input to `UpdateNutritionNotesHandler`.

A separate command from `UpdateNutritionCommand`, matching
`Nutrition.update_notes()` being its own aggregate method with its own
event (`MealNotesUpdated`) — the same "one command per named aggregate
method" shape `UpdateWaterCommand`
(`app.application.nutrition.commands.update_water`) establishes for
`Nutrition.update_water()`, and `UpdateNotesCommand`
(`app.application.progress.commands.update_notes`) establishes for
`Progress.update_notes()`. `notes` is required, not optional:
`Nutrition.update_notes(notes: MealNotes, ...)` takes no optional/"leave
unchanged" form, so neither does this command.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.application.shared.command import Command
from app.domain.nutrition.identifiers import NutritionId
from app.domain.nutrition.value_objects import MealNotes
from app.domain.user.identifiers import UserId


@dataclass(frozen=True, kw_only=True)
class UpdateNutritionNotesCommand(Command):
    """Replace an existing Nutrition entry's notes wholesale.

    `requester_id` is the authenticated caller — see
    `app.application.nutrition.queries.get_nutrition.GetNutritionQuery`'s
    own module docstring for the full ownership-check reasoning, which
    applies identically here.
    """

    nutrition_id: NutritionId
    requester_id: UserId
    notes: MealNotes
