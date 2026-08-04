"""`CancelGoalCommand`: the input to `CancelGoalHandler`."""

from __future__ import annotations

from dataclasses import dataclass

from app.application.shared.command import Command
from app.domain.goal.identifiers import GoalId


@dataclass(frozen=True, kw_only=True)
class CancelGoalCommand(Command):
    """Cancel an existing, Active Goal."""

    goal_id: GoalId
