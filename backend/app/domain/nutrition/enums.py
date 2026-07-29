"""Closed-set categorical values used by the Nutrition aggregate.

Neither enum is a verbatim Domain Model & Decision Engine Bible table —
the Bible's closest concept, `Meal` (Section 4.9, Table 12), has an
`input_type` field (how the entry was captured) but no fixed
breakfast/lunch/dinner/snack classification and no direct analog of
`NutritionSource`. Both are this increment's own addition, grounded in the
task's own explicit list. See `nutrition.py`'s module docstring and
`docs/adr/0011-nutrition-is-a-per-entry-log-not-a-daily-rollup.md` for why
neither field is required on `Nutrition`.

Both inherit `str` as well as `Enum` so a member serializes to exactly its
`.value` wherever it's written to JSON, a database column, or an event
payload — the same convention every other enum in this codebase follows.
"""

from enum import Enum


class MealType(str, Enum):
    """Which meal of the day a `Nutrition` entry is associated with, when
    known. `Nutrition.meal_type` is `MealType | None` — not every entry
    cleanly maps to one of these four (e.g. a whole-day estimate, or a
    grazing pattern that doesn't fit a single meal) — see the module
    docstring for why this isn't a required field.
    """

    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"


class NutritionSource(str, Enum):
    """How a `Nutrition` entry's values were obtained. Loosely parallels
    `app.domain.progress.enums.ProgressSource`'s reasoning (provenance
    matters to future consumers weighing entries), but with values scoped
    to how food intake specifically gets logged rather than reused
    verbatim from `Progress`.
    """

    MANUAL = "manual"
    BARCODE = "barcode"
    IMPORT = "import"
