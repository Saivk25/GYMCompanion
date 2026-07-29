"""The persistence contract for the Exercise aggregate.

Adds nothing beyond the shared kernel's `Repository[TAggregate, TId]`
(`get`/`add`/`remove`), matching `UserRepository`/`WorkoutRepository`'s own
discipline: no query method here (e.g. "find every Active exercise for a
given `MovementPattern`", the obvious candidate once Plan generation or
Substitution exist) is grounded in a concrete caller in this codebase yet.
Both of those callers — and the graph-traversal queries a real Knowledge
Graph needs — belong to a later increment this task explicitly excludes.
`app/infra/` provides the real, Postgres-backed implementation.
"""

from app.domain.exercise.exercise import Exercise
from app.domain.exercise.identifiers import ExerciseId
from app.domain.shared_kernel.repository import Repository


class ExerciseRepository(Repository[Exercise, ExerciseId]):
    """Persistence contract for the Exercise aggregate. See the module
    docstring for why it declares no methods beyond the shared kernel's.
    """
