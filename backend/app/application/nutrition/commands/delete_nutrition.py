"""`DeleteNutritionCommand`: the input to `DeleteNutritionHandler`.

The first command in this codebase to remove an aggregate outright
rather than mutate it in place — `Nutrition` has no soft-delete/status
concept the way `User`/`Workout` do (`nutrition.py`'s module docstring:
"No status enum and no lifecycle... a logged entry is a fact captured
at a point in time"), and no `NutritionDeleted` event exists on the
aggregate (`events.py` is scoped to exactly the four events
`record()`/`update_nutrition()`/`update_water()`/`update_notes()`
raise). Deleting a logged entry outright — correcting a mis-logged meal
— is therefore a `NutritionRepository.remove()` call, not an aggregate
method invocation; see `DeleteNutritionHandler` for the consequence
this has for event dispatch.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.application.shared.command import Command
from app.domain.nutrition.identifiers import NutritionId


@dataclass(frozen=True, kw_only=True)
class DeleteNutritionCommand(Command):
    """Permanently remove an existing Nutrition entry."""

    nutrition_id: NutritionId
