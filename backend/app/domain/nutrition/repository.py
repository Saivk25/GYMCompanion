"""The persistence contract for the Nutrition aggregate.

Adds nothing beyond the shared kernel's `Repository[TAggregate, TId]`
(`get`/`add`/`remove`), matching every other aggregate's repository in this
codebase: no query method here (e.g. "find every Nutrition entry for a
User on a given date" — the obvious candidate for a daily-total read
model) is grounded in a concrete caller in this codebase yet. `app/infra/`
provides the real, Postgres-backed implementation.
"""

from app.domain.nutrition.identifiers import NutritionId
from app.domain.nutrition.nutrition import Nutrition
from app.domain.shared_kernel.repository import Repository


class NutritionRepository(Repository[Nutrition, NutritionId]):
    """Persistence contract for the Nutrition aggregate. See the module
    docstring for why it declares no methods beyond the shared kernel's.
    """
