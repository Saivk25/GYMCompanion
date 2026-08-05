"""HTTP routes for the Workout and WorkoutSession modules — ten
endpoints, one per Application Handler in `app.application.workout.
handlers`. See `goal.py`'s module docstring for what every route here
does and does not do.

Two aggregates, one router — mirroring `app/api/schemas/workout.py`'s
own pairing (see that module's docstring): `WorkoutSession` has no
Application Layer module of its own separate from `Workout`'s.

| Method | Path                                            | Handler                     |
|--------|--------------------------------------------------|-------------------------------|
| POST   | /api/v1/workouts                                  | CreateWorkoutHandler           |
| GET    | /api/v1/workouts/{workout_id}                     | GetWorkoutHandler              |
| GET    | /api/v1/workouts                                  | ListWorkoutsHandler            |
| PATCH  | /api/v1/workouts/{workout_id}                     | UpdateWorkoutHandler           |
| POST   | /api/v1/workouts/{workout_id}/cancel              | CancelWorkoutHandler           |
| POST   | /api/v1/workouts/{workout_id}/sessions            | StartWorkoutSessionHandler     |
| GET    | /api/v1/workout-sessions/{session_id}             | GetWorkoutSessionHandler       |
| POST   | /api/v1/workout-sessions/{session_id}/complete    | CompleteWorkoutSessionHandler  |
| POST   | /api/v1/workout-sessions/{session_id}/sets        | LogExerciseSetHandler          |
| POST   | /api/v1/workout-sessions/{session_id}/sets/complete | CompleteExerciseSetHandler   |
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.deps import handler_dependency
from app.api.errors import unwrap_or_400, unwrap_or_404, unwrap_or_500
from app.api.schemas.common import IdResponse
from app.api.schemas.workout import (
    CompleteExerciseSetRequest,
    CompleteWorkoutSessionRequest,
    CreateWorkoutRequest,
    LogExerciseSetRequest,
    StartWorkoutSessionRequest,
    UpdateWorkoutRequest,
    WorkoutResponse,
    WorkoutSessionResponse,
)
from app.application.workout.commands.cancel_workout import CancelWorkoutCommand
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
from app.application.workout.queries.get_workout import GetWorkoutQuery
from app.application.workout.queries.get_workout_session import GetWorkoutSessionQuery
from app.application.workout.queries.list_workouts import ListWorkoutsQuery
from app.domain.user.identifiers import UserId
from app.domain.workout.identifiers import WorkoutId
from app.domain.workout_session.identifiers import WorkoutSessionId

router = APIRouter(tags=["workouts"])

_get_create_handler = handler_dependency(CreateWorkoutHandler)
_get_get_handler = handler_dependency(GetWorkoutHandler)
_get_list_handler = handler_dependency(ListWorkoutsHandler)
_get_update_handler = handler_dependency(UpdateWorkoutHandler)
_get_cancel_handler = handler_dependency(CancelWorkoutHandler)
_get_start_session_handler = handler_dependency(StartWorkoutSessionHandler)
_get_get_session_handler = handler_dependency(GetWorkoutSessionHandler)
_get_complete_session_handler = handler_dependency(CompleteWorkoutSessionHandler)
_get_log_set_handler = handler_dependency(LogExerciseSetHandler)
_get_complete_set_handler = handler_dependency(CompleteExerciseSetHandler)


# ---------------------------------------------------------------------------
# Workout
# ---------------------------------------------------------------------------


@router.post("/workouts", response_model=IdResponse, status_code=status.HTTP_201_CREATED)
def create_workout(
    body: CreateWorkoutRequest, handler: CreateWorkoutHandler = Depends(_get_create_handler)
) -> IdResponse:
    result = handler.handle(body.to_command())
    workout_id = unwrap_or_400(result)
    return IdResponse(id=str(workout_id), warnings=result.warnings)


@router.get("/workouts/{workout_id}", response_model=WorkoutResponse)
def get_workout(
    workout_id: str, handler: GetWorkoutHandler = Depends(_get_get_handler)
) -> WorkoutResponse:
    result = handler.handle(GetWorkoutQuery(workout_id=WorkoutId.parse(workout_id)))
    return WorkoutResponse.from_dto(unwrap_or_404(result))


@router.get("/workouts", response_model=list[WorkoutResponse])
def list_workouts(
    user_id: str, handler: ListWorkoutsHandler = Depends(_get_list_handler)
) -> list[WorkoutResponse]:
    result = handler.handle(ListWorkoutsQuery(user_id=UserId.parse(user_id)))
    return [WorkoutResponse.from_dto(dto) for dto in unwrap_or_500(result)]


@router.patch("/workouts/{workout_id}", response_model=IdResponse)
def update_workout(
    workout_id: str,
    body: UpdateWorkoutRequest,
    handler: UpdateWorkoutHandler = Depends(_get_update_handler),
) -> IdResponse:
    result = handler.handle(body.to_command(WorkoutId.parse(workout_id)))
    updated_id = unwrap_or_400(result)
    return IdResponse(id=str(updated_id), warnings=result.warnings)


@router.post("/workouts/{workout_id}/cancel", response_model=IdResponse)
def cancel_workout(
    workout_id: str, handler: CancelWorkoutHandler = Depends(_get_cancel_handler)
) -> IdResponse:
    result = handler.handle(CancelWorkoutCommand(workout_id=WorkoutId.parse(workout_id)))
    cancelled_id = unwrap_or_400(result)
    return IdResponse(id=str(cancelled_id), warnings=result.warnings)


# ---------------------------------------------------------------------------
# WorkoutSession
# ---------------------------------------------------------------------------


@router.post(
    "/workouts/{workout_id}/sessions",
    response_model=IdResponse,
    status_code=status.HTTP_201_CREATED,
)
def start_workout_session(
    workout_id: str,
    body: StartWorkoutSessionRequest,
    handler: StartWorkoutSessionHandler = Depends(_get_start_session_handler),
) -> IdResponse:
    result = handler.handle(body.to_command(WorkoutId.parse(workout_id)))
    session_id = unwrap_or_400(result)
    return IdResponse(id=str(session_id), warnings=result.warnings)


@router.get("/workout-sessions/{session_id}", response_model=WorkoutSessionResponse)
def get_workout_session(
    session_id: str, handler: GetWorkoutSessionHandler = Depends(_get_get_session_handler)
) -> WorkoutSessionResponse:
    result = handler.handle(GetWorkoutSessionQuery(session_id=WorkoutSessionId.parse(session_id)))
    return WorkoutSessionResponse.from_dto(unwrap_or_404(result))


@router.post("/workout-sessions/{session_id}/complete", response_model=IdResponse)
def complete_workout_session(
    session_id: str,
    body: CompleteWorkoutSessionRequest,
    handler: CompleteWorkoutSessionHandler = Depends(_get_complete_session_handler),
) -> IdResponse:
    result = handler.handle(body.to_command(WorkoutSessionId.parse(session_id)))
    completed_id = unwrap_or_400(result)
    return IdResponse(id=str(completed_id), warnings=result.warnings)


@router.post(
    "/workout-sessions/{session_id}/sets",
    response_model=IdResponse,
    status_code=status.HTTP_201_CREATED,
)
def log_exercise_set(
    session_id: str,
    body: LogExerciseSetRequest,
    handler: LogExerciseSetHandler = Depends(_get_log_set_handler),
) -> IdResponse:
    result = handler.handle(body.to_command(WorkoutSessionId.parse(session_id)))
    performance_id = unwrap_or_400(result)
    return IdResponse(id=str(performance_id), warnings=result.warnings)


@router.post("/workout-sessions/{session_id}/sets/complete", response_model=IdResponse)
def complete_exercise_set(
    session_id: str,
    body: CompleteExerciseSetRequest,
    handler: CompleteExerciseSetHandler = Depends(_get_complete_set_handler),
) -> IdResponse:
    result = handler.handle(body.to_command(WorkoutSessionId.parse(session_id)))
    updated_session_id = unwrap_or_400(result)
    return IdResponse(id=str(updated_session_id), warnings=result.warnings)
