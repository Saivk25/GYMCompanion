"""Closed-set categorical values used by the Readiness aggregate.

Not a verbatim Domain Model & Decision Engine Bible table — the Bible's
closest concept, `ReadinessCheckIn` (Section 4.8, Table 11), names no
provenance field at all; every check-in is described as "entirely
user-reported." `ReadinessSource` is this increment's own addition,
grounded in the task's explicit list and the same reasoning
`app.domain.progress.enums.ProgressSource` and
`app.domain.nutrition.enums.NutritionSource` already establish: knowing
whether a value was typed by hand or synced from a wearable matters to
future consumers weighing observations, particularly for something as
device-friendly as sleep/HRV/resting heart rate data.

Inherits `str` as well as `Enum` so a member serializes to exactly its
`.value` wherever it's written to JSON, a database column, or an event
payload — the same convention every other enum in this codebase follows.
"""

from enum import Enum


class ReadinessSource(str, Enum):
    """How a `Readiness` entry's values were obtained."""

    MANUAL = "manual"
    WEARABLE = "wearable"
    IMPORTED = "imported"
