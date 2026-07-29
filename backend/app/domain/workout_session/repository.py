"""The persistence contract for the WorkoutSession aggregate.

Adds nothing beyond the shared kernel's `Repository[TAggregate, TId]`
(`get`/`add`/`remove`), matching `UserRepository`/`WorkoutRepository`/
`ExerciseRepository`'s own discipline: no query method here (e.g. "find
every session for a Workout", "find every session for a User in a date
range" — the obvious candidates for a workout-history view) is grounded in
a concrete caller in this codebase yet. `app/infra/` provides the real,
Postgres-backed implementation.
"""

from app.domain.shared_kernel.repository import Repository
from app.domain.workout_session.identifiers import WorkoutSessionId
from app.domain.workout_session.workout_session import WorkoutSession


class WorkoutSessionRepository(Repository[WorkoutSession, WorkoutSessionId]):
    """Persistence contract for the WorkoutSession aggregate. See the
    module docstring for why it declares no methods beyond the shared
    kernel's.
    """
