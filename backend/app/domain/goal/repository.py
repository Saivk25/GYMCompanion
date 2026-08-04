"""The persistence contract for the Goal aggregate.

Beyond the shared kernel's `Repository[TAggregate, TId]` (`get`/`add`/
`remove`), also declares `list_by_user()` — added in Sprint 4's Goal
Application Use Cases phase for `ListGoalsHandler`
(`app.application.goal`), the first concrete caller needing "every Goal
for a User." This is the exact extension this module's own prior
docstring anticipated ("no query method here... is grounded in a
concrete caller in this codebase yet"), the identical shape
`WorkoutRepository.list_by_user()` (`docs/adr/0024-workout-application-
use-cases.md`), `NutritionRepository.list_by_user()` (`docs/adr/0025`),
`ProgressRepository.list_by_user()` (`docs/adr/0026`), and
`ReadinessRepository.list_by_user()` (`docs/adr/0027`) already
established — see `docs/adr/0028-goal-application-use-cases.md`.

Still no "find every Active Goal for a User, ranked by priority" method
— real priority-ranking/conflict-resolution logic across a user's
concurrent goals remains out of scope (see `goal.py`'s own module
docstring and `docs/adr/0012`); `list_by_user()` returns every Goal
regardless of status, and a caller that needs only Active ones filters
the result itself. `app/infra/` provides the real, Postgres-backed
implementation of both methods.
"""

from abc import abstractmethod
from collections.abc import Sequence

from app.domain.goal.goal import Goal
from app.domain.goal.identifiers import GoalId
from app.domain.shared_kernel.repository import Repository
from app.domain.user.identifiers import UserId


class GoalRepository(Repository[Goal, GoalId]):
    """Persistence contract for the Goal aggregate. See the module
    docstring for `list_by_user()`.
    """

    @abstractmethod
    def list_by_user(self, user_id: UserId) -> Sequence[Goal]:
        """Returns every Goal belonging to `user_id`, regardless of
        status, in no guaranteed order — a concrete implementation may
        return them in whatever order is cheapest; a caller that needs a
        specific order (or only Active goals) is responsible for
        sorting/filtering the result itself, the same "caller-supplied
        ordering, not implied by this interface" trust every sibling
        `list_by_user()` in this codebase already established. Returns
        an empty sequence, never `None`, when the user has no goals.
        """
        raise NotImplementedError  # pragma: no cover — abstract, always overridden
