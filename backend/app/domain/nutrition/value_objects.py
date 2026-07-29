"""Immutable value objects owned by the Nutrition aggregate.

Every type here is a `ValueObject` subclass (`app.domain.shared_kernel`):
no identity, replaced wholesale on change, validated once at construction —
the same discipline every other aggregate's value objects follow.

`Calories`/`Protein`/`Carbohydrates`/`Fat`/`Fiber`/`Sugar`/`WaterIntake` all
require `>= 0`, not `> 0` — deliberately different from
`app.domain.progress.value_objects`'s body-measurement value objects
(`BodyWeight`, `WaistMeasurement`, etc.), which require strictly positive
values. Zero is a completely ordinary nutrition value (a food with no fat,
a fasting day with zero calories logged, a meal with no added sugar) —
rejecting it would reject legitimate data, unlike a body measurement of
zero, which cannot describe a real body.

Each numeric value object is still its own distinct type, not a shared
"non-negative float" wrapper — the same primitive-obsession reasoning
`app.domain.progress.value_objects`'s module docstring documents,
applied here: a caller passing `Fat` where `Protein` is expected is a type
error mypy catches, not a silent unit-confusion bug.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.domain.shared_kernel.validation import ensure
from app.domain.shared_kernel.value_object import ValueObject

_MAX_MEAL_NOTES_LENGTH = 2000


def _ensure_not_negative(value: float, field_name: str) -> None:
    """Shared guard for every `>= 0` value object below. Not promoted to
    `app.domain.shared_kernel.validation` (which only has `ensure_positive`,
    a strict `> 0` check) — this module is the only place in the codebase
    that needs a `>= 0` bound so far; see that module's own docstring on
    staying deliberately small until a second real caller needs the same
    shape of check.
    """
    ensure(value >= 0, f"{field_name} must not be negative, got {value}")


@dataclass(frozen=True)
class NutritionDate(ValueObject):
    """The calendar date this nutrition entry was logged for — a
    `datetime.date`, not a `datetime`, the same reasoning
    `app.domain.progress.value_objects.ProgressDate` documents. "Nutrition
    date required" is enforced by `Nutrition` requiring one at
    construction, not by any extra validation here — every `date` value is
    a valid `NutritionDate`.
    """

    value: date


@dataclass(frozen=True)
class Calories(ValueObject):
    """Energy content, in kilocalories. "Calories >= 0.\""""

    value: float

    def __post_init__(self) -> None:
        _ensure_not_negative(self.value, "calories")


@dataclass(frozen=True)
class Protein(ValueObject):
    """Protein content, in grams. "Protein >= 0.\""""

    value: float

    def __post_init__(self) -> None:
        _ensure_not_negative(self.value, "protein")


@dataclass(frozen=True)
class Carbohydrates(ValueObject):
    """Carbohydrate content, in grams. "Carbohydrates >= 0.\""""

    value: float

    def __post_init__(self) -> None:
        _ensure_not_negative(self.value, "carbohydrates")


@dataclass(frozen=True)
class Fat(ValueObject):
    """Fat content, in grams. "Fat >= 0.\""""

    value: float

    def __post_init__(self) -> None:
        _ensure_not_negative(self.value, "fat")


@dataclass(frozen=True)
class Fiber(ValueObject):
    """Fiber content, in grams. "Fiber >= 0.\""""

    value: float

    def __post_init__(self) -> None:
        _ensure_not_negative(self.value, "fiber")


@dataclass(frozen=True)
class Sugar(ValueObject):
    """Sugar content, in grams. "Sugar >= 0.\""""

    value: float

    def __post_init__(self) -> None:
        _ensure_not_negative(self.value, "sugar")


@dataclass(frozen=True)
class WaterIntake(ValueObject):
    """Water intake, in milliliters. "Water intake >= 0." Tracked
    separately from the macro fields above (its own `update_water()`
    method and `WaterUpdated` event on `Nutrition`) — the Domain Model &
    Decision Engine Bible keeps `Hydration` as its own entity distinct
    from `Meal` (Section 4, Table 2: "Nutrition | Meal, FoodItem,
    NutritionPattern, Hydration, Supplement"), and this increment mirrors
    that separation within one aggregate rather than folding water into
    the same update as calories/protein/etc.
    """

    value: float

    def __post_init__(self) -> None:
        _ensure_not_negative(self.value, "water_intake")


@dataclass(frozen=True)
class MealNotes(ValueObject):
    """Free-text notes on this nutrition entry. "Notes may be empty" — the
    same "empty is a valid value, not `None`" discipline as
    `app.domain.progress.value_objects.ProgressNotes` and
    `app.domain.workout_session.value_objects.SessionNotes`:
    `Nutrition.notes` is never `None`, only ever a `MealNotes` that may
    happen to be empty.
    """

    value: str = ""

    def __post_init__(self) -> None:
        ensure(
            len(self.value) <= _MAX_MEAL_NOTES_LENGTH,
            f"meal notes must be at most {_MAX_MEAL_NOTES_LENGTH} characters, "
            f"got {len(self.value)}",
        )
