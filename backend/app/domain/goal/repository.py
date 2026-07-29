"""The persistence contract for the Goal aggregate.

Adds nothing beyond the shared kernel's `Repository[TAggregate, TId]`
(`get`/`add`/`remove`), matching every other aggregate's repository in this
codebase: no query method here (e.g. "find every Active Goal for a User,
ranked by priority" — the obvious candidate once real ranking/conflict
logic exists) is grounded in a concrete caller in this codebase yet.
`app/infra/` provides the real, Postgres-backed implementation.
"""

from app.domain.goal.goal import Goal
from app.domain.goal.identifiers import GoalId
from app.domain.shared_kernel.repository import Repository


class GoalRepository(Repository[Goal, GoalId]):
    """Persistence contract for the Goal aggregate. See the module
    docstring for why it declares no methods beyond the shared kernel's.
    """
