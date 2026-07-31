"""The persistence contract for the WorkoutSession aggregate.

Beyond the shared kernel's `Repository[TAggregate, TId]` (`get`/`add`/
`remove`), also declares `list_by_user()` — added in Sprint 4, Phase 3
(`app.application.workout`) for `CompleteWorkoutSessionHandler`, which
needs a user's session history to build a
`ProgressiveOverloadRuleContext`/`TrainingLoadRuleContext` (both
require *many* sessions, not one). This is the exact extension this
module's own prior docstring anticipated ("find every session for a
User... [is] the obvious candidate... [not yet] grounded in a concrete
caller") — see `docs/adr/0024-workout-application-use-cases.md`. "Find
every session for a Workout" remains ungrounded and is not added here.
`app/infra/` provides the real, Postgres-backed implementation of both
methods.
"""

from abc import abstractmethod
from collections.abc import Sequence

from app.domain.shared_kernel.repository import Repository
from app.domain.user.identifiers import UserId
from app.domain.workout_session.identifiers import WorkoutSessionId
from app.domain.workout_session.workout_session import WorkoutSession


class WorkoutSessionRepository(Repository[WorkoutSession, WorkoutSessionId]):
    """Persistence contract for the WorkoutSession aggregate. See the
    module docstring for `list_by_user()`.
    """

    @abstractmethod
    def list_by_user(self, user_id: UserId) -> Sequence[WorkoutSession]:
        """Returns every WorkoutSession belonging to `user_id`, in no
        guaranteed order — see `WorkoutRepository.list_by_user()`'s
        identical note on caller-supplied ordering. Returns an empty
        sequence, never `None`, when the user has no sessions.
        """
        raise NotImplementedError  # pragma: no cover — abstract, always overridden
