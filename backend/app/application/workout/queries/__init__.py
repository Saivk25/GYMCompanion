"""Immutable query objects for the Workout Application Use Cases."""

from app.application.workout.queries.get_workout import GetWorkoutQuery
from app.application.workout.queries.get_workout_session import GetWorkoutSessionQuery
from app.application.workout.queries.list_workouts import ListWorkoutsQuery

__all__ = ["GetWorkoutQuery", "GetWorkoutSessionQuery", "ListWorkoutsQuery"]
