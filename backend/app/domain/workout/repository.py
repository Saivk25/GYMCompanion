"""The persistence contract for the Workout aggregate.

Adds nothing beyond the shared kernel's `Repository[TAggregate, TId]`
(`get`/`add`/`remove`), matching `app.domain.user.repository.UserRepository`'s
own discipline: no query method here (e.g. "list every Workout for a
User", the obvious candidate for a workout-history view) is grounded in a
concrete caller in this codebase yet — add one only once a real caller
needs it, not speculatively. `app/infra/` provides the real, Postgres-
backed implementation.
"""

from app.domain.shared_kernel.repository import Repository
from app.domain.workout.identifiers import WorkoutId
from app.domain.workout.workout import Workout


class WorkoutRepository(Repository[Workout, WorkoutId]):
    """Persistence contract for the Workout aggregate. See the module
    docstring for why it declares no methods beyond the shared kernel's.
    """
