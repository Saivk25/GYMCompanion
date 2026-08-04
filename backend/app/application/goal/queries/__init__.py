"""Immutable query objects for the Goal Application Use Cases."""

from app.application.goal.queries.get_goal import GetGoalQuery
from app.application.goal.queries.list_goals import ListGoalsQuery

__all__ = ["GetGoalQuery", "ListGoalsQuery"]
