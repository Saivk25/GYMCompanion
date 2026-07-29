"""Domain events raised by the Nutrition aggregate.

Scoped to exactly the four events this increment's task named —
`NutritionRecorded`, `NutritionUpdated`, `WaterUpdated`,
`MealNotesUpdated` — the same "raise only what the aggregate's own methods
actually do" discipline every other aggregate's `events.py` already
follows.

`NutritionUpdated` covers `calories`/`protein`/`carbohydrates`/`fat`/
`fiber`/`sugar` together (one event for all six, mirroring
`app.domain.progress.events.BodyCompositionUpdated`'s "one event per
named update method" shape); `WaterUpdated` is separate, matching
`Nutrition.update_water()` being its own method — see
`value_objects.py`'s `WaterIntake` docstring for why water is tracked
apart from the other macro fields. Both `*Updated` events carry the full
resulting value of every field in their group, not just what changed in
one call — the same choice `BodyCompositionUpdated`/`MeasurementsUpdated`
make, for the same reason: a downstream reader needs a coherent snapshot,
not a diff it would have to reconstruct history to make sense of.
"""

from dataclasses import dataclass

from app.domain.nutrition.enums import MealType, NutritionSource
from app.domain.nutrition.identifiers import NutritionId
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
from app.domain.shared_kernel.events import DomainEvent
from app.domain.user.identifiers import UserId


@dataclass(frozen=True, kw_only=True)
class NutritionRecorded(DomainEvent):
    """A new Nutrition entry was created via `Nutrition.record(...)`.
    Carries the identifying fields a first subscriber would need without
    re-fetching the aggregate; macro/water values are covered by
    `NutritionUpdated`/`WaterUpdated` when set, including when set as
    part of the same `record()` call — see `nutrition.py`'s class
    docstring.
    """

    nutrition_id: NutritionId
    user_id: UserId
    nutrition_date: NutritionDate
    meal_type: MealType | None
    source: NutritionSource | None


@dataclass(frozen=True, kw_only=True)
class NutritionUpdated(DomainEvent):
    """`Nutrition.update_nutrition(...)` changed one or more of
    `calories`/`protein`/`carbohydrates`/`fat`/`fiber`/`sugar`. Carries the
    resulting value of all six (each still `None` if never set), not just
    the ones this call changed — see the module docstring.
    """

    nutrition_id: NutritionId
    user_id: UserId
    calories: Calories | None
    protein: Protein | None
    carbohydrates: Carbohydrates | None
    fat: Fat | None
    fiber: Fiber | None
    sugar: Sugar | None


@dataclass(frozen=True, kw_only=True)
class WaterUpdated(DomainEvent):
    """`Nutrition.update_water(...)` replaced `water_intake`."""

    nutrition_id: NutritionId
    user_id: UserId
    water_intake: WaterIntake


@dataclass(frozen=True, kw_only=True)
class MealNotesUpdated(DomainEvent):
    """`Nutrition.update_notes(...)` replaced this entry's notes. Carries
    the full new `notes`, the same choice
    `app.domain.progress.events.ProgressNotesUpdated` makes.
    """

    nutrition_id: NutritionId
    user_id: UserId
    notes: MealNotes
