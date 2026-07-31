"""`GetWorkoutSessionHandler`: fetches one WorkoutSession's current
state as a `WorkoutSessionDTO`.

Same read-side shape as `GetWorkoutHandler`. See
`docs/adr/0024-workout-application-use-cases.md`.
"""

from __future__ import annotations

from app.application.shared.application_result import ApplicationResult
from app.application.shared.query_handler import QueryHandler
from app.application.shared.unit_of_work import UnitOfWork
from app.application.workout.dto.workout_session_dto import WorkoutSessionDTO
from app.application.workout.queries.get_workout_session import GetWorkoutSessionQuery
from app.domain.workout_session.repository import WorkoutSessionRepository
from app.domain.workout_session.workout_session import WorkoutSession


class GetWorkoutSessionHandler(QueryHandler[GetWorkoutSessionQuery, WorkoutSessionDTO]):
    """Loads a WorkoutSession and returns it as a `WorkoutSessionDTO`, or
    a failed `ApplicationResult` if no such session exists."""

    def __init__(self, *, uow: UnitOfWork) -> None:
        self._uow = uow

    def handle(self, request: GetWorkoutSessionQuery) -> ApplicationResult[WorkoutSessionDTO]:
        # `session` is initialized before the `try` (not inside it) so it is
        # always definitely assigned below — see `GetWorkoutHandler`'s
        # identical reasoning.
        session: WorkoutSession | None = None
        try:
            with self._uow as uow:
                # WorkoutSessionRepository has no concrete implementation in
                # this phase (by design); mypy's type-abstract check assumes a
                # type[T] argument might be instantiated, but get_repository
                # only ever uses it as a lookup key, so this is a documented,
                # narrow false positive.
                repository = uow.get_repository(
                    WorkoutSessionRepository  # type: ignore[type-abstract]
                )
                session = repository.get(request.session_id)
        except Exception as exc:
            return ApplicationResult.fail([str(exc)])

        if session is None:
            return ApplicationResult.fail([f"workout session {request.session_id} not found"])

        return ApplicationResult.ok(WorkoutSessionDTO.from_workout_session(session))
