"""`ListGoalsHandler`: lists every Goal belonging to one User, as
`GoalDTO`s.

The first real caller of `GoalRepository.list_by_user()` — see that
method's own docstring (`app.domain.goal.repository`) and
`docs/adr/0028-goal-application-use-cases.md`. Read-side, same shape as
`app.application.readiness.handlers.list_readiness_handler.
ListReadinessHandler`. Returns every Goal regardless of status — see
`GoalRepository.list_by_user()`'s own docstring for why no Active-only
filtering happens here; a caller that wants only Active goals filters
the result itself.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.application.goal.dto.goal_dto import GoalDTO
from app.application.goal.queries.list_goals import ListGoalsQuery
from app.application.shared.application_result import ApplicationResult
from app.application.shared.query_handler import QueryHandler
from app.application.shared.unit_of_work import UnitOfWork
from app.domain.goal.goal import Goal
from app.domain.goal.repository import GoalRepository


class ListGoalsHandler(QueryHandler[ListGoalsQuery, tuple[GoalDTO, ...]]):
    """Loads every Goal for a User and returns them as `GoalDTO`s, in
    whatever order `list_by_user()` returns (see that method's own
    docstring — no ordering is implied or applied here)."""

    def __init__(self, *, uow: UnitOfWork) -> None:
        self._uow = uow

    def handle(self, request: ListGoalsQuery) -> ApplicationResult[tuple[GoalDTO, ...]]:
        # `goals` is initialized before the `try` (not inside it) so it
        # is always definitely assigned below — see `GetGoalHandler`'s
        # identical reasoning; `()` is itself a legitimate result (a user
        # with no goals), not just a typing placeholder.
        goals: Sequence[Goal] = ()
        try:
            with self._uow as uow:
                # GoalRepository has no concrete implementation in this
                # phase (by design); mypy's type-abstract check assumes a
                # type[T] argument might be instantiated, but get_repository
                # only ever uses it as a lookup key, so this is a documented,
                # narrow false positive.
                repository = uow.get_repository(GoalRepository)  # type: ignore[type-abstract]
                goals = repository.list_by_user(request.user_id)
        except Exception as exc:
            return ApplicationResult.fail([str(exc)])

        return ApplicationResult.ok(tuple(GoalDTO.from_goal(goal) for goal in goals))
