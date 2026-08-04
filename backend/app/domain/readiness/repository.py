"""The persistence contract for the Readiness aggregate.

Beyond the shared kernel's `Repository[TAggregate, TId]` (`get`/`add`/
`remove`), also declares `list_by_user()` — added in Sprint 4, Phase 6
(`app.application.readiness`) for its one concrete caller,
`ListReadinessHandler`. This is the exact extension this module's own
prior docstring anticipated ("no query method here... is grounded in a
concrete caller in this codebase yet"), the identical shape
`WorkoutRepository.list_by_user()`, `NutritionRepository.list_by_user()`,
and `ProgressRepository.list_by_user()` already established — see
`docs/adr/0027-readiness-application-use-cases.md`. It does not, by
itself, enforce the Bible's "one check-in per day" rule (still a future
application/repository-layer concern — see `readiness.py`'s module
docstring); it only returns every check-in for a user. `app/infra/`
provides the real, Postgres-backed implementation of every method.
"""

from abc import abstractmethod
from collections.abc import Sequence

from app.domain.readiness.identifiers import ReadinessId
from app.domain.readiness.readiness import Readiness
from app.domain.shared_kernel.repository import Repository
from app.domain.user.identifiers import UserId


class ReadinessRepository(Repository[Readiness, ReadinessId]):
    """Persistence contract for the Readiness aggregate. See the module
    docstring for `list_by_user()`.
    """

    @abstractmethod
    def list_by_user(self, user_id: UserId) -> Sequence[Readiness]:
        """Returns every Readiness check-in belonging to `user_id`, in no
        guaranteed order — a concrete implementation may return them in
        whatever order is cheapest; a caller that needs a specific order
        is responsible for sorting the result itself, the same
        "caller-supplied ordering, not implied by this interface" trust
        `WorkoutRepository.list_by_user()`/`NutritionRepository.
        list_by_user()`/`ProgressRepository.list_by_user()` already
        established. Returns an empty sequence, never `None`, when the
        user has no check-ins.
        """
        raise NotImplementedError  # pragma: no cover — abstract, always overridden
