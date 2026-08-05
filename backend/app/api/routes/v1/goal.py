"""HTTP routes for the Goal module — six endpoints, one per Application
Handler in `app.application.goal.handlers`.

| Method | Path                        | Handler               |
|--------|-----------------------------|------------------------|
| POST   | /api/v1/goals               | CreateGoalHandler       |
| GET    | /api/v1/goals/{goal_id}     | GetGoalHandler          |
| GET    | /api/v1/goals               | ListGoalsHandler        |
| PATCH  | /api/v1/goals/{goal_id}     | UpdateGoalHandler       |
| POST   | /api/v1/goals/{goal_id}/complete | CompleteGoalHandler |
| POST   | /api/v1/goals/{goal_id}/cancel   | CancelGoalHandler   |

Every route here does exactly three things: convert the HTTP request
into a Command/Query via a schema's own `to_command()`/direct
construction, resolve the one handler it needs via `handler_dependency`,
and convert the resulting `ApplicationResult` into an HTTP response via
one of `app.api.errors`'s `unwrap_or_*` helpers — no business logic, no
repository access, no SQLAlchemy models, matching this phase's own
stated rules.

**Every route requires authentication** (`Depends(get_current_user_id)`,
`app/api/deps.py`) — added in the Authentication & Authorization phase.
`create_goal` and `list_goals` use the returned `UserId` to build their
Command/Query (replacing what used to be a client-supplied `user_id`
field/query-param — a caller can no longer create or list goals on
another user's behalf). The four routes addressing a specific
`goal_id` (`get_goal`, `update_goal`, `complete_goal`, `cancel_goal`)
depend on it only to require *a* valid caller, binding the result to
`_user_id` — this phase does not yet verify the caller actually *owns*
that `goal_id`; see `docs/adr/0032-authentication-and-authorization.md`
for that gap, named there as a deliberate, scoped technical debt item.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.deps import get_current_user_id, handler_dependency
from app.api.errors import unwrap_or_400, unwrap_or_404, unwrap_or_500
from app.api.schemas.common import IdResponse
from app.api.schemas.goal import CreateGoalRequest, GoalResponse, UpdateGoalRequest
from app.application.goal.commands.cancel_goal import CancelGoalCommand
from app.application.goal.commands.complete_goal import CompleteGoalCommand
from app.application.goal.handlers.cancel_goal_handler import CancelGoalHandler
from app.application.goal.handlers.complete_goal_handler import CompleteGoalHandler
from app.application.goal.handlers.create_goal_handler import CreateGoalHandler
from app.application.goal.handlers.get_goal_handler import GetGoalHandler
from app.application.goal.handlers.list_goals_handler import ListGoalsHandler
from app.application.goal.handlers.update_goal_handler import UpdateGoalHandler
from app.application.goal.queries.get_goal import GetGoalQuery
from app.application.goal.queries.list_goals import ListGoalsQuery
from app.domain.goal.identifiers import GoalId
from app.domain.user.identifiers import UserId

router = APIRouter(prefix="/goals", tags=["goals"])

_get_create_handler = handler_dependency(CreateGoalHandler)
_get_get_handler = handler_dependency(GetGoalHandler)
_get_list_handler = handler_dependency(ListGoalsHandler)
_get_update_handler = handler_dependency(UpdateGoalHandler)
_get_complete_handler = handler_dependency(CompleteGoalHandler)
_get_cancel_handler = handler_dependency(CancelGoalHandler)


@router.post("", response_model=IdResponse, status_code=status.HTTP_201_CREATED)
def create_goal(
    body: CreateGoalRequest,
    user_id: UserId = Depends(get_current_user_id),
    handler: CreateGoalHandler = Depends(_get_create_handler),
) -> IdResponse:
    result = handler.handle(body.to_command(user_id))
    goal_id = unwrap_or_400(result)
    return IdResponse(id=str(goal_id), warnings=result.warnings)


@router.get("/{goal_id}", response_model=GoalResponse)
def get_goal(
    goal_id: str,
    _user_id: UserId = Depends(get_current_user_id),
    handler: GetGoalHandler = Depends(_get_get_handler),
) -> GoalResponse:
    result = handler.handle(GetGoalQuery(goal_id=GoalId.parse(goal_id)))
    return GoalResponse.from_dto(unwrap_or_404(result))


@router.get("", response_model=list[GoalResponse])
def list_goals(
    user_id: UserId = Depends(get_current_user_id),
    handler: ListGoalsHandler = Depends(_get_list_handler),
) -> list[GoalResponse]:
    result = handler.handle(ListGoalsQuery(user_id=user_id))
    return [GoalResponse.from_dto(dto) for dto in unwrap_or_500(result)]


@router.patch("/{goal_id}", response_model=IdResponse)
def update_goal(
    goal_id: str,
    body: UpdateGoalRequest,
    _user_id: UserId = Depends(get_current_user_id),
    handler: UpdateGoalHandler = Depends(_get_update_handler),
) -> IdResponse:
    result = handler.handle(body.to_command(GoalId.parse(goal_id)))
    updated_id = unwrap_or_400(result)
    return IdResponse(id=str(updated_id), warnings=result.warnings)


@router.post("/{goal_id}/complete", response_model=IdResponse)
def complete_goal(
    goal_id: str,
    _user_id: UserId = Depends(get_current_user_id),
    handler: CompleteGoalHandler = Depends(_get_complete_handler),
) -> IdResponse:
    result = handler.handle(CompleteGoalCommand(goal_id=GoalId.parse(goal_id)))
    completed_id = unwrap_or_400(result)
    return IdResponse(id=str(completed_id), warnings=result.warnings)


@router.post("/{goal_id}/cancel", response_model=IdResponse)
def cancel_goal(
    goal_id: str,
    _user_id: UserId = Depends(get_current_user_id),
    handler: CancelGoalHandler = Depends(_get_cancel_handler),
) -> IdResponse:
    result = handler.handle(CancelGoalCommand(goal_id=GoalId.parse(goal_id)))
    cancelled_id = unwrap_or_400(result)
    return IdResponse(id=str(cancelled_id), warnings=result.warnings)
