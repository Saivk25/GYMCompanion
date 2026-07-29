"""The Nutrition aggregate root.

The canonical representation of a user's nutrition intake: one logged
entry — dated, optionally tied to a specific meal — carrying calories,
macros, water intake, and notes. Domain Model & Decision Engine Bible,
Section 4.9's `Meal` ("a single logged eating event", Table 12) is the
closest analog; this increment deliberately does not build `Meal`'s AI
assessment pipeline, `FoodItem` references, confidence scoring, or
Logged -> Assessed -> Confirmed/Disputed lifecycle — none of that is asked
for here, and the task's own "Do NOT implement" list rules out the food
database and barcode lookup those would depend on.

This aggregate stores canonical nutrition information only. It does not
compute meal plans, calorie targets, macro targets, or recommendations —
those read this aggregate's events, never the other way around (the same
relationship `app.domain.progress.progress`'s module docstring describes
between `Progress` and Progress Intelligence).

One `Nutrition` record is one logged entry, not a rolled-up daily total —
see `docs/adr/0011-nutrition-is-a-per-entry-log-not-a-daily-rollup.md` for
the full reasoning and why `meal_type`/`source` are optional rather than
required. Computing "today's total calories" from a set of `Nutrition`
records for one user/date is a future read-model's job, the same way
`Progress` doesn't compute trends over its own history.

Tenant-scoped like every other per-user aggregate in this codebase
(carries `user_id`).

No status enum and no lifecycle, the same shape as `Progress`: a logged
entry is a fact captured at a point in time. Unlike `Progress`, this
task's Rules list includes no immutability statement at all, so
`update_nutrition()`/`update_water()`/`update_notes()` carry no special
policy caveat beyond being ordinary, unconditionally-callable mutations.
"""

from __future__ import annotations

from datetime import datetime

from app.domain.nutrition.enums import MealType, NutritionSource
from app.domain.nutrition.events import (
    MealNotesUpdated,
    NutritionRecorded,
    NutritionUpdated,
    WaterUpdated,
)
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
from app.domain.shared_kernel.aggregate_root import AggregateRoot
from app.domain.shared_kernel.clock import Clock
from app.domain.shared_kernel.validation import ensure
from app.domain.user.identifiers import UserId


class Nutrition(AggregateRoot[NutritionId]):
    """The Nutrition aggregate. See the module docstring for scope and the
    ADR for the per-entry-not-daily-rollup reasoning.

    Construct a brand-new entry via the `record()` factory, never
    `Nutrition(...)` directly — the constructor is also used to rehydrate
    an existing entry from a repository, where re-raising
    `NutritionRecorded` would be wrong.
    """

    def __init__(
        self,
        nutrition_id: NutritionId,
        *,
        user_id: UserId,
        nutrition_date: NutritionDate,
        recorded_at: datetime,
        meal_type: MealType | None = None,
        source: NutritionSource | None = None,
        calories: Calories | None = None,
        protein: Protein | None = None,
        carbohydrates: Carbohydrates | None = None,
        fat: Fat | None = None,
        fiber: Fiber | None = None,
        sugar: Sugar | None = None,
        water_intake: WaterIntake | None = None,
        notes: MealNotes | None = None,
        updated_at: datetime | None = None,
    ) -> None:
        super().__init__(nutrition_id)
        ensure(recorded_at.tzinfo is not None, "recorded_at must be timezone-aware")
        self._user_id = user_id
        self._nutrition_date = nutrition_date
        self._recorded_at = recorded_at
        self._meal_type = meal_type
        self._source = source
        self._calories = calories
        self._protein = protein
        self._carbohydrates = carbohydrates
        self._fat = fat
        self._fiber = fiber
        self._sugar = sugar
        self._water_intake = water_intake
        self._notes = notes if notes is not None else MealNotes()
        self._updated_at = updated_at

    @classmethod
    def record(
        cls,
        *,
        nutrition_id: NutritionId,
        user_id: UserId,
        nutrition_date: NutritionDate,
        clock: Clock,
        meal_type: MealType | None = None,
        source: NutritionSource | None = None,
        calories: Calories | None = None,
        protein: Protein | None = None,
        carbohydrates: Carbohydrates | None = None,
        fat: Fat | None = None,
        fiber: Fiber | None = None,
        sugar: Sugar | None = None,
        water_intake: WaterIntake | None = None,
        notes: MealNotes | None = None,
    ) -> Nutrition:
        """Creates a brand-new Nutrition entry and records
        `NutritionRecorded`. `nutrition_id` is generated by the caller
        (`NutritionId.generate()`) before calling this — the same
        convention every other aggregate's factory follows.

        Every macro/water field can be supplied here directly (the common
        case: a single entry where everything was captured at once) or
        filled in afterward via `update_nutrition()`/`update_water()` —
        both are equally valid.
        """
        recorded_at = clock.now()
        nutrition = cls(
            nutrition_id,
            user_id=user_id,
            nutrition_date=nutrition_date,
            recorded_at=recorded_at,
            meal_type=meal_type,
            source=source,
            calories=calories,
            protein=protein,
            carbohydrates=carbohydrates,
            fat=fat,
            fiber=fiber,
            sugar=sugar,
            water_intake=water_intake,
            notes=notes,
        )
        nutrition.record_event(
            NutritionRecorded(
                occurred_at=recorded_at,
                nutrition_id=nutrition_id,
                user_id=user_id,
                nutrition_date=nutrition_date,
                meal_type=meal_type,
                source=source,
            )
        )
        return nutrition

    @property
    def user_id(self) -> UserId:
        return self._user_id

    @property
    def nutrition_date(self) -> NutritionDate:
        return self._nutrition_date

    @property
    def recorded_at(self) -> datetime:
        return self._recorded_at

    @property
    def meal_type(self) -> MealType | None:
        return self._meal_type

    @property
    def source(self) -> NutritionSource | None:
        return self._source

    @property
    def calories(self) -> Calories | None:
        return self._calories

    @property
    def protein(self) -> Protein | None:
        return self._protein

    @property
    def carbohydrates(self) -> Carbohydrates | None:
        return self._carbohydrates

    @property
    def fat(self) -> Fat | None:
        return self._fat

    @property
    def fiber(self) -> Fiber | None:
        return self._fiber

    @property
    def sugar(self) -> Sugar | None:
        return self._sugar

    @property
    def water_intake(self) -> WaterIntake | None:
        return self._water_intake

    @property
    def notes(self) -> MealNotes:
        return self._notes

    @property
    def updated_at(self) -> datetime | None:
        return self._updated_at

    def update_nutrition(
        self,
        *,
        clock: Clock,
        calories: Calories | None = None,
        protein: Protein | None = None,
        carbohydrates: Carbohydrates | None = None,
        fat: Fat | None = None,
        fiber: Fiber | None = None,
        sugar: Sugar | None = None,
    ) -> None:
        """Replaces whichever macro/calorie fields are given (`None` means
        "leave unchanged", the same convention
        `app.domain.progress.progress.Progress.update_body_composition()`
        uses) and records one `NutritionUpdated` carrying the resulting
        value of all six fields.
        """
        if calories is not None:
            self._calories = calories
        if protein is not None:
            self._protein = protein
        if carbohydrates is not None:
            self._carbohydrates = carbohydrates
        if fat is not None:
            self._fat = fat
        if fiber is not None:
            self._fiber = fiber
        if sugar is not None:
            self._sugar = sugar
        self._updated_at = clock.now()
        self.record_event(
            NutritionUpdated(
                occurred_at=self._updated_at,
                nutrition_id=self.id,
                user_id=self._user_id,
                calories=self._calories,
                protein=self._protein,
                carbohydrates=self._carbohydrates,
                fat=self._fat,
                fiber=self._fiber,
                sugar=self._sugar,
            )
        )

    def update_water(self, water_intake: WaterIntake, *, clock: Clock) -> None:
        """Replaces `water_intake` wholesale and records one
        `WaterUpdated` — separate from `update_nutrition()`, see
        `value_objects.py`'s `WaterIntake` docstring for why.
        """
        self._water_intake = water_intake
        self._updated_at = clock.now()
        self.record_event(
            WaterUpdated(
                occurred_at=self._updated_at,
                nutrition_id=self.id,
                user_id=self._user_id,
                water_intake=water_intake,
            )
        )

    def update_notes(self, notes: MealNotes, *, clock: Clock) -> None:
        """Replaces this entry's notes wholesale and records one
        `MealNotesUpdated`."""
        self._notes = notes
        self._updated_at = clock.now()
        self.record_event(
            MealNotesUpdated(
                occurred_at=self._updated_at,
                nutrition_id=self.id,
                user_id=self._user_id,
                notes=notes,
            )
        )
