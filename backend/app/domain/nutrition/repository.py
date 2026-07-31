"""The persistence contract for the Nutrition aggregate.

Beyond the shared kernel's `Repository[TAggregate, TId]` (`get`/`add`/
`remove`), also declares `list_by_user()` — added in Sprint 4, Phase 4
(`app.application.nutrition`) for `ListNutritionHandler`, the first
concrete caller needing "every Nutrition entry for a User." This is the
exact extension this module's own prior docstring anticipated ("no
query method here... is grounded in a concrete caller in this codebase
yet") — see `docs/adr/0025-nutrition-application-use-cases.md`, which
also explains why this still isn't the daily-total read model a future
`NutritionPattern`-equivalent aggregate would need: `list_by_user()`
returns every entry for a user, unfiltered and unsummed, leaving any
date-scoping or rollup to the caller. `app/infra/` provides the real,
Postgres-backed implementation of both methods.
"""

from abc import abstractmethod
from collections.abc import Sequence

from app.domain.nutrition.identifiers import NutritionId
from app.domain.nutrition.nutrition import Nutrition
from app.domain.shared_kernel.repository import Repository
from app.domain.user.identifiers import UserId


class NutritionRepository(Repository[Nutrition, NutritionId]):
    """Persistence contract for the Nutrition aggregate. See the module
    docstring for `list_by_user()`.
    """

    @abstractmethod
    def list_by_user(self, user_id: UserId) -> Sequence[Nutrition]:
        """Returns every Nutrition entry belonging to `user_id`, in no
        guaranteed order — a concrete implementation may return them in
        whatever order is cheapest; a caller that needs a specific order
        (e.g. by `nutrition_date`) is responsible for sorting the result
        itself, the same "caller-supplied ordering, not implied by this
        interface" trust `WorkoutRepository.list_by_user()`
        (`app.domain.workout.repository`) already established for the
        identical shape of method. Returns an empty sequence, never
        `None`, when the user has no entries.
        """
        raise NotImplementedError  # pragma: no cover — abstract, always overridden
