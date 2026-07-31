"""Handlers for the Workout Application Use Cases. See
`docs/adr/0024-workout-application-use-cases.md`.
"""

from app.application.workout.handlers.cancel_workout_handler import CancelWorkoutHandler
from app.application.workout.handlers.complete_exercise_set_handler import (
    CompleteExerciseSetHandler,
)
from app.application.workout.handlers.complete_workout_session_handler import (
    CompleteWorkoutSessionHandler,
)
from app.application.workout.handlers.create_workout_handler import CreateWorkoutHandler
from app.application.workout.handlers.get_workout_handler import GetWorkoutHandler
from app.application.workout.handlers.get_workout_session_handler import GetWorkoutSessionHandler
from app.application.workout.handlers.list_workouts_handler import ListWorkoutsHandler
from app.application.workout.handlers.log_exercise_set_handler import LogExerciseSetHandler
from app.application.workout.handlers.start_workout_session_handler import (
    StartWorkoutSessionHandler,
)
from app.application.workout.handlers.update_workout_handler import UpdateWorkoutHandler

__all__ = [
    "CancelWorkoutHandler",
    "CompleteExerciseSetHandler",
    "CompleteWorkoutSessionHandler",
    "CreateWorkoutHandler",
    "GetWorkoutHandler",
    "GetWorkoutSessionHandler",
    "ListWorkoutsHandler",
    "LogExerciseSetHandler",
    "StartWorkoutSessionHandler",
    "UpdateWorkoutHandler",
]
