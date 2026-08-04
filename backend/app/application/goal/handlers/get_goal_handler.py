"""`GetGoalHandler`: fetches one Goal's current state as a `GoalDTO`.

Same read-side shape as `app.application.readiness.handlers.
get_readiness_handler.GetReadinessHandler` — no `Clock`, no
`DomainEventDispatcher`, no `commit()`.
"""

from __future__ import annotations

from app.application.goal.dto.goal_dto import GoalDTO
from app.application.goal.queries.get_goal import GetGoalQuery
from app.application.shared.application_result import ApplicationResult
from app.application.shared.query_handler import QueryHandler
from app.application.shared.unit_of_work import UnitOfWork
from app.domain.goal.goal import Goal
from app.domain.goal.repository import GoalRepository


class GetGoalHandler(QueryHandler[GetGoalQuery, GoalDTO]):
    """Loads a Goal and returns it as a `GoalDTO`, or a failed
    `ApplicationResult` if no such goal exists."""

    def __init__(self, *, uow: UnitOfWork) -> None:
        self._uow = uow

    def handle(self, request: GetGoalQuery) -> ApplicationResult[GoalDTO]:
        # `goal` is initialized before the `try` (not inside it) so it is
        # always definitely assigned below — see `GetReadinessHandler`'s
        # identical reasoning.
        goal: Goal | None = None
        try:
            with self._uow as uow:
                # GoalRepository has no concrete implementation in this
                # phase (by design); mypy's type-abstract check assumes a
                # type[T] argument might be instantiated, but get_repository
                # only ever uses it as a lookup key, so this is a documented,
                # narrow false positive.
                repository = uow.get_repository(GoalRepository)  # type: ignore[type-abstract]
                goal = repository.get(request.goal_id)
        except Exception as exc:
            return ApplicationResult.fail([str(exc)])

        if goal is None:
            return ApplicationResult.fail([f"goal {request.goal_id} not found"])

        return ApplicationResult.ok(GoalDTO.from_goal(goal))
