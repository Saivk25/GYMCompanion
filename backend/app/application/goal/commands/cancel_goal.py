"""`CancelGoalCommand`: the input to `CancelGoalHandler`."""

from __future__ import annotations

from dataclasses import dataclass

from app.application.shared.command import Command
from app.domain.goal.identifiers import GoalId
from app.domain.user.identifiers import UserId


@dataclass(frozen=True, kw_only=True)
class CancelGoalCommand(Command):
    """Cancel an existing, Active Goal.

    `requester_id` is the authenticated caller — see
    `app.application.goal.queries.get_goal.GetGoalQuery`'s own module
    docstring for the full ownership-check reasoning, which applies
    identically here.
    """

    goal_id: GoalId
    requester_id: UserId
