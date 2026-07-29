"""The Nutrition aggregate: Sprint 2's sixth real aggregate, built on the
Sprint 1 shared kernel (`app.domain.shared_kernel`) and following the same
pattern as `app.domain.user`, `app.domain.workout`, `app.domain.exercise`,
`app.domain.workout_session`, and `app.domain.progress`. Nutrition bounded
context (Domain Model & Decision Engine Bible, Section 3, Table 2), closest
deep dive in Section 4.9 (`Meal`).

The canonical representation of a user's nutrition intake: one logged
entry — dated, optionally tied to a specific meal — carrying calories,
macros, water intake, and notes. Stores facts only — no meal planning,
food database, barcode lookup, recommendations, macro targets, or calorie
targets. Those belong to a future NutritionPattern-equivalent read model
and Plan generation, neither built yet.

See `docs/adr/0011-nutrition-is-a-per-entry-log-not-a-daily-rollup.md` for
why one `Nutrition` record is one logged entry rather than a rolled-up
daily total, and why `meal_type`/`source` are optional.

Depends on nothing outside the Python standard library,
`app.domain.shared_kernel`, and `app.domain.user` (for the owning
`UserId`) — enforced by the same statically-checked rule as the rest of
`app/domain` (`tests/domain/test_import_boundaries.py`).
"""

from app.domain.nutrition.context import NutritionContext
from app.domain.nutrition.enums import MealType, NutritionSource
from app.domain.nutrition.events import (
    MealNotesUpdated,
    NutritionRecorded,
    NutritionUpdated,
    WaterUpdated,
)
from app.domain.nutrition.identifiers import NutritionId
from app.domain.nutrition.nutrition import Nutrition
from app.domain.nutrition.repository import NutritionRepository
from app.domain.nutrition.value_objects import (
    Calories,
    Carbohydrates,
    Fat,
    Fiber,
    MealNotes,
    NutritionDate,
    Protein,
    Sugar,
    WaterIntake,
)

__all__ = [
    "Calories",
    "Carbohydrates",
    "Fat",
    "Fiber",
    "MealNotes",
    "MealNotesUpdated",
    "MealType",
    "Nutrition",
    "NutritionContext",
    "NutritionDate",
    "NutritionId",
    "NutritionRecorded",
    "NutritionRepository",
    "NutritionSource",
    "NutritionUpdated",
    "Protein",
    "Sugar",
    "WaterIntake",
    "WaterUpdated",
]
