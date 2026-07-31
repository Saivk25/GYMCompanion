"""The persistence contract for the Workout aggregate.

Beyond the shared kernel's `Repository[TAggregate, TId]` (`get`/`add`/
`remove`), also declares `list_by_user()` — added in Sprint 4, Phase 3
(`app.application.workout`) for `ListWorkoutsHandler`, the first
concrete caller needing "every Workout for a User." This is the exact
extension this module's own prior docstring anticipated ("add one only
once a real caller needs it, not speculatively") — see
`docs/adr/0024-workout-application-use-cases.md`. `app/infra/`
provides the real, Postgres-backed implementation of both methods.
"""

from abc import abstractmethod
from collections.abc import Sequence

from app.domain.shared_kernel.repository import Repository
from app.domain.user.identifiers import UserId
from app.domain.workout.identifiers import WorkoutId
from app.domain.workout.workout import Workout


class WorkoutRepository(Repository[Workout, WorkoutId]):
    """Persistence contract for the Workout aggregate. See the module
    docstring for `list_by_user()`.
    """

    @abstractmethod
    def list_by_user(self, user_id: UserId) -> Sequence[Workout]:
        """Returns every Workout belonging to `user_id`, in no
        guaranteed order — a concrete implementation may return them in
        whatever order is cheapest (e.g. insertion/primary-key order);
        a caller that needs a specific order (e.g. by `planned_date`)
        is responsible for sorting the result itself, the same
        "caller-supplied ordering, not implied by this interface" trust
        `TrainingLoadRuleContext.from_summaries()` places in its own
        caller. Returns an empty sequence, never `None`, when the user
        has no workouts.
        """
        raise NotImplementedError  # pragma: no cover — abstract, always overridden
