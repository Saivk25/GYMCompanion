"""`UpdateNutritionCommand`: the input to `UpdateNutritionHandler`.

**`None` means "leave unchanged," not "clear" — the opposite
convention from `app.application.workout.commands.update_workout.
UpdateWorkoutCommand`.** This is not an inconsistency between the two
commands; each mirrors its own aggregate method's already-established
semantics exactly: `Workout.update_goal()`/`update_notes()` are
full-replace (`None` is a legitimate stored value, "no goal"), while
`Nutrition.update_nutrition(...)`'s own docstring is explicit that "`
None` means 'leave unchanged'" (`nutrition.py`). A command's job is to
carry a caller's intent through to the aggregate method it invokes
unmodified — inventing a different, command-level meaning for `None`
here would silently contradict what `Nutrition.update_nutrition()`
itself already documents.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.application.shared.command import Command
from app.domain.nutrition.identifiers import NutritionId
from app.domain.nutrition.value_objects import Calories, Carbohydrates, Fat, Fiber, Protein, Sugar
from app.domain.user.identifiers import UserId


@dataclass(frozen=True, kw_only=True)
class UpdateNutritionCommand(Command):
    """Replace whichever macro/calorie fields are given on an existing
    Nutrition entry; a field left `None` keeps its current stored
    value.

    `requester_id` is the authenticated caller — see
    `app.application.nutrition.queries.get_nutrition.GetNutritionQuery`'s
    own module docstring for the full ownership-check reasoning, which
    applies identically here.
    """

    nutrition_id: NutritionId
    requester_id: UserId
    calories: Calories | None = None
    protein: Protein | None = None
    carbohydrates: Carbohydrates | None = None
    fat: Fat | None = None
    fiber: Fiber | None = None
    sugar: Sugar | None = None
