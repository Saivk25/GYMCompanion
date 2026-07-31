"""`ListWorkoutsHandler`: lists every Workout belonging to one User, as
`WorkoutDTO`s.

The first real caller of `WorkoutRepository.list_by_user()` — see that
method's own docstring (`app.domain.workout.repository`) and
`docs/adr/0024-workout-application-use-cases.md`. Read-side, same shape
as `GetWorkoutHandler`.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.application.shared.application_result import ApplicationResult
from app.application.shared.query_handler import QueryHandler
from app.application.shared.unit_of_work import UnitOfWork
from app.application.workout.dto.workout_dto import WorkoutDTO
from app.application.workout.queries.list_workouts import ListWorkoutsQuery
from app.domain.workout.repository import WorkoutRepository
from app.domain.workout.workout import Workout


class ListWorkoutsHandler(QueryHandler[ListWorkoutsQuery, tuple[WorkoutDTO, ...]]):
    """Loads every Workout for a User and returns them as `WorkoutDTO`s,
    in whatever order `list_by_user()` returns (see that method's own
    docstring — no ordering is implied or applied here)."""

    def __init__(self, *, uow: UnitOfWork) -> None:
        self._uow = uow

    def handle(self, request: ListWorkoutsQuery) -> ApplicationResult[tuple[WorkoutDTO, ...]]:
        # `workouts` is initialized before the `try` (not inside it) so it is
        # always definitely assigned below — see `GetWorkoutHandler`'s
        # identical reasoning; `()` is itself a legitimate result (a user
        # with no workouts), not just a typing placeholder.
        workouts: Sequence[Workout] = ()
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
                workouts = repository.list_by_user(request.user_id)
        except Exception as exc:
            return ApplicationResult.fail([str(exc)])

        return ApplicationResult.ok(tuple(WorkoutDTO.from_workout(workout) for workout in workouts))
