"""Handlers for the Goal Application Use Cases. See
`docs/adr/0028-goal-application-use-cases.md`.
"""

from app.application.goal.handlers.cancel_goal_handler import CancelGoalHandler
from app.application.goal.handlers.complete_goal_handler import CompleteGoalHandler
from app.application.goal.handlers.create_goal_handler import CreateGoalHandler
from app.application.goal.handlers.get_goal_handler import GetGoalHandler
from app.application.goal.handlers.list_goals_handler import ListGoalsHandler
from app.application.goal.handlers.update_goal_handler import UpdateGoalHandler

__all__ = [
    "CancelGoalHandler",
    "CompleteGoalHandler",
    "CreateGoalHandler",
    "GetGoalHandler",
    "ListGoalsHandler",
    "UpdateGoalHandler",
]
