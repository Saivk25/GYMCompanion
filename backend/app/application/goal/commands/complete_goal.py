"""`CompleteGoalCommand`: the input to `CompleteGoalHandler`."""

from __future__ import annotations

from dataclasses import dataclass

from app.application.shared.command import Command
from app.domain.goal.identifiers import GoalId


@dataclass(frozen=True, kw_only=True)
class CompleteGoalCommand(Command):
    """Mark an existing, Active Goal as Completed."""

    goal_id: GoalId
