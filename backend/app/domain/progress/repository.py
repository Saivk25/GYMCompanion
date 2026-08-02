"""The persistence contract for the Progress aggregate.

Beyond the shared kernel's `Repository[TAggregate, TId]` (`get`/`add`/
`remove`), also declares `list_by_user()` — added in Sprint 4, Phase 5
(`app.application.progress`) for two concrete callers:
`ListProgressHandler` (a direct listing) and every handler that evaluates
`ProgressEvaluationRuleEngine` (`RecordProgressHandler`,
`UpdateBodyCompositionHandler`, `UpdateMeasurementsHandler`), which need
a user's full check-in history to build a `ProgressEvaluationRuleContext`
— see `docs/adr/0026-progress-application-use-cases.md`. This is the
exact extension this module's own prior docstring anticipated ("no query
method here... is grounded in a concrete caller in this codebase yet"),
the identical shape `WorkoutRepository.list_by_user()`
(`docs/adr/0024-workout-application-use-cases.md`) and
`NutritionRepository.list_by_user()` (`docs/adr/0025-nutrition-
application-use-cases.md`) already established. `app/infra/` provides
the real, Postgres-backed implementation of every method.

Deliberately still no `update` — see `progress.py`'s class docstring and
`docs/adr/0010-progress-immutability-is-a-policy-not-a-guard.md` for why
that omission does not, by itself, enforce this aggregate's immutability
rule (every other aggregate's repository is shaped identically and none of
them are meant to be immutable).
"""

from abc import abstractmethod
from collections.abc import Sequence

from app.domain.progress.identifiers import ProgressId
from app.domain.progress.progress import Progress
from app.domain.shared_kernel.repository import Repository
from app.domain.user.identifiers import UserId


class ProgressRepository(Repository[Progress, ProgressId]):
    """Persistence contract for the Progress aggregate. See the module
    docstring for `list_by_user()`.
    """

    @abstractmethod
    def list_by_user(self, user_id: UserId) -> Sequence[Progress]:
        """Returns every Progress record belonging to `user_id`, in no
        guaranteed order — a concrete implementation may return them in
        whatever order is cheapest; a caller that needs a specific order
        (e.g. chronological, by `progress_date`) is responsible for
        sorting the result itself, the same "caller-supplied ordering,
        not implied by this interface" trust `WorkoutRepository.
        list_by_user()`/`NutritionRepository.list_by_user()` already
        established for the identical shape of method —
        `ProgressEvaluationRuleContext.from_aggregates()`
        (`app.domain.progress.rules.context`) is one such caller that
        does its own chronological sort. Returns an empty sequence,
        never `None`, when the user has no records.
        """
        raise NotImplementedError  # pragma: no cover — abstract, always overridden
