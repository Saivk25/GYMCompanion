"""The Goal aggregate: Sprint 2's eighth real aggregate, built on the
Sprint 1 shared kernel (`app.domain.shared_kernel`) and following the same
pattern as every other aggregate in `app.domain`. Training bounded context
(Domain Model & Decision Engine Bible, Section 3, Table 2), closest deep
dive in Section 4.4 (`Goal`).

The canonical representation of a user's fitness objectives. Stores goals
only — no plans, recommendations, readiness, analytics, or AI suggestions.
Those belong to Plan generation and the future rule engines named in this
increment's own Goal statement, none built yet.

See `docs/adr/0012-goal-lifecycle-and-expired-with-no-transition.md` for
why `GoalStatus` is smaller than the Bible's own six-state lifecycle and
why `EXPIRED` exists as a status value with no method that transitions
into it.

Depends on nothing outside the Python standard library,
`app.domain.shared_kernel`, and `app.domain.user` (for the owning
`UserId`) — enforced by the same statically-checked rule as the rest of
`app/domain` (`tests/domain/test_import_boundaries.py`).
"""

from app.domain.goal.context import GoalContext
from app.domain.goal.enums import GoalStatus, GoalType
from app.domain.goal.events import GoalCancelled, GoalCompleted, GoalCreated, GoalUpdated
from app.domain.goal.goal import Goal
from app.domain.goal.identifiers import GoalId
from app.domain.goal.repository import GoalRepository
from app.domain.goal.value_objects import (
    GoalDescription,
    GoalName,
    GoalNotes,
    Priority,
    TargetBodyFat,
    TargetDate,
    TargetStrength,
    TargetWeight,
)

__all__ = [
    "Goal",
    "GoalCancelled",
    "GoalCompleted",
    "GoalContext",
    "GoalCreated",
    "GoalDescription",
    "GoalId",
    "GoalName",
    "GoalNotes",
    "GoalRepository",
    "GoalStatus",
    "GoalType",
    "GoalUpdated",
    "Priority",
    "TargetBodyFat",
    "TargetDate",
    "TargetStrength",
    "TargetWeight",
]
