"""`GetGoalQuery`: the input to `GetGoalHandler`."""

from __future__ import annotations

from dataclasses import dataclass

from app.application.shared.query import Query
from app.domain.goal.identifiers import GoalId
from app.domain.user.identifiers import UserId


@dataclass(frozen=True, kw_only=True)
class GetGoalQuery(Query):
    """Fetch one Goal's current state as a `GoalDTO`.

    `requester_id` is the authenticated caller (`app.api.deps.
    get_current_user_id`, threaded through by `app.api.routes.v1.goal.
    get_goal`) — `GetGoalHandler` compares it against the loaded Goal's
    own `user_id` via `app.application.shared.ownership.ensure_owner`
    before returning it, and fails with `ApplicationResult.forbid(...)`
    on a mismatch. See `docs/adr/0033-resource-ownership-
    authorization.md`.
    """

    goal_id: GoalId
    requester_id: UserId
