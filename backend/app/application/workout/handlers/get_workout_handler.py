"""`GetWorkoutHandler`: fetches one Workout's current state as a
`WorkoutDTO`.

Same read-side shape as `app.application.user.handlers.
get_user_handler.GetUserHandler` — no `Clock`, no
`DomainEventDispatcher`, no `commit()`. See
`docs/adr/0024-workout-application-use-cases.md`.
"""

from __future__ import annotations

from app.application.shared.application_result import ApplicationResult
from app.application.shared.ownership import ensure_owner
from app.application.shared.query_handler import QueryHandler
from app.application.shared.unit_of_work import UnitOfWork
from app.application.workout.dto.workout_dto import WorkoutDTO
from app.application.workout.queries.get_workout import GetWorkoutQuery
from app.domain.workout.repository import WorkoutRepository
from app.domain.workout.workout import Workout


class GetWorkoutHandler(QueryHandler[GetWorkoutQuery, WorkoutDTO]):
    """Loads a Workout and returns it as a `WorkoutDTO`, or a failed
    `ApplicationResult` if no such workout exists."""

    def __init__(self, *, uow: UnitOfWork) -> None:
        self._uow = uow

    def handle(self, request: GetWorkoutQuery) -> ApplicationResult[WorkoutDTO]:
        # `workout` is initialized before the `try` (not inside it) so it is
        # always definitely assigned below — see the identical reasoning in
        # `GetUserHandler`.
        workout: Workout | None = None
        try:
            with self._uow as uow:
                # WorkoutRepository has no concrete implementation in this phase
                # (by design); mypy's type-abstract check assumes a type[T]
                # argument might be instantiated, but get_repository only ever
                # uses it as a lookup key, so this is a documented, narrow
                # false positive.
                repository = uow.get_repository(
                    WorkoutRepository  # type: ignore[type-abstract]
                )
                workout = repository.get(request.workout_id)
        except Exception as exc:
            return ApplicationResult.fail([str(exc)])

        if workout is None:
            return ApplicationResult.fail([f"workout {request.workout_id} not found"])

        denial = ensure_owner(owner_id=workout.user_id, requester_id=request.requester_id)
        if denial is not None:
            return ApplicationResult.forbid([denial])

        return ApplicationResult.ok(WorkoutDTO.from_workout(workout))
