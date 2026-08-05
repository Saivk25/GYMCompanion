"""HTTP routes for the Readiness module — seven endpoints, one per
Application Handler in `app.application.readiness.handlers`. See
`goal.py`'s module docstring for what every route here does and does
not do.

| Method | Path                                          | Handler                    |
|--------|-----------------------------------------------|------------------------------|
| POST   | /api/v1/readiness                             | RecordReadinessHandler        |
| GET    | /api/v1/readiness/{readiness_id}              | GetReadinessHandler           |
| GET    | /api/v1/readiness                             | ListReadinessHandler          |
| PUT    | /api/v1/readiness/{readiness_id}/sleep        | UpdateSleepHandler             |
| PUT    | /api/v1/readiness/{readiness_id}/recovery-metrics | UpdateRecoveryMetricsHandler |
| PUT    | /api/v1/readiness/{readiness_id}/notes        | UpdateNotesHandler              |
| DELETE | /api/v1/readiness/{readiness_id}              | DeleteReadinessHandler          |
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.deps import handler_dependency
from app.api.errors import unwrap_or_400, unwrap_or_404, unwrap_or_500
from app.api.schemas.common import IdResponse
from app.api.schemas.readiness import (
    ReadinessResponse,
    RecordReadinessRequest,
    UpdateReadinessNotesRequest,
    UpdateRecoveryMetricsRequest,
    UpdateSleepRequest,
)
from app.application.readiness.commands.delete_readiness import DeleteReadinessCommand
from app.application.readiness.handlers.delete_readiness_handler import DeleteReadinessHandler
from app.application.readiness.handlers.get_readiness_handler import GetReadinessHandler
from app.application.readiness.handlers.list_readiness_handler import ListReadinessHandler
from app.application.readiness.handlers.record_readiness_handler import RecordReadinessHandler
from app.application.readiness.handlers.update_notes_handler import UpdateNotesHandler
from app.application.readiness.handlers.update_recovery_metrics_handler import (
    UpdateRecoveryMetricsHandler,
)
from app.application.readiness.handlers.update_sleep_handler import UpdateSleepHandler
from app.application.readiness.queries.get_readiness import GetReadinessQuery
from app.application.readiness.queries.list_readiness import ListReadinessQuery
from app.domain.readiness.identifiers import ReadinessId
from app.domain.user.identifiers import UserId

router = APIRouter(prefix="/readiness", tags=["readiness"])

_get_record_handler = handler_dependency(RecordReadinessHandler)
_get_get_handler = handler_dependency(GetReadinessHandler)
_get_list_handler = handler_dependency(ListReadinessHandler)
_get_update_sleep_handler = handler_dependency(UpdateSleepHandler)
_get_update_recovery_metrics_handler = handler_dependency(UpdateRecoveryMetricsHandler)
_get_update_notes_handler = handler_dependency(UpdateNotesHandler)
_get_delete_handler = handler_dependency(DeleteReadinessHandler)


@router.post("", response_model=IdResponse, status_code=status.HTTP_201_CREATED)
def record_readiness(
    body: RecordReadinessRequest, handler: RecordReadinessHandler = Depends(_get_record_handler)
) -> IdResponse:
    result = handler.handle(body.to_command())
    readiness_id = unwrap_or_400(result)
    return IdResponse(id=str(readiness_id), warnings=result.warnings)


@router.get("/{readiness_id}", response_model=ReadinessResponse)
def get_readiness(
    readiness_id: str, handler: GetReadinessHandler = Depends(_get_get_handler)
) -> ReadinessResponse:
    result = handler.handle(GetReadinessQuery(readiness_id=ReadinessId.parse(readiness_id)))
    return ReadinessResponse.from_dto(unwrap_or_404(result))


@router.get("", response_model=list[ReadinessResponse])
def list_readiness(
    user_id: str, handler: ListReadinessHandler = Depends(_get_list_handler)
) -> list[ReadinessResponse]:
    result = handler.handle(ListReadinessQuery(user_id=UserId.parse(user_id)))
    return [ReadinessResponse.from_dto(dto) for dto in unwrap_or_500(result)]


@router.put("/{readiness_id}/sleep", response_model=IdResponse)
def update_sleep(
    readiness_id: str,
    body: UpdateSleepRequest,
    handler: UpdateSleepHandler = Depends(_get_update_sleep_handler),
) -> IdResponse:
    result = handler.handle(body.to_command(ReadinessId.parse(readiness_id)))
    updated_id = unwrap_or_400(result)
    return IdResponse(id=str(updated_id), warnings=result.warnings)


@router.put("/{readiness_id}/recovery-metrics", response_model=IdResponse)
def update_recovery_metrics(
    readiness_id: str,
    body: UpdateRecoveryMetricsRequest,
    handler: UpdateRecoveryMetricsHandler = Depends(_get_update_recovery_metrics_handler),
) -> IdResponse:
    result = handler.handle(body.to_command(ReadinessId.parse(readiness_id)))
    updated_id = unwrap_or_400(result)
    return IdResponse(id=str(updated_id), warnings=result.warnings)


@router.put("/{readiness_id}/notes", response_model=IdResponse)
def update_readiness_notes(
    readiness_id: str,
    body: UpdateReadinessNotesRequest,
    handler: UpdateNotesHandler = Depends(_get_update_notes_handler),
) -> IdResponse:
    result = handler.handle(body.to_command(ReadinessId.parse(readiness_id)))
    updated_id = unwrap_or_400(result)
    return IdResponse(id=str(updated_id), warnings=result.warnings)


@router.delete("/{readiness_id}", response_model=IdResponse)
def delete_readiness(
    readiness_id: str, handler: DeleteReadinessHandler = Depends(_get_delete_handler)
) -> IdResponse:
    result = handler.handle(DeleteReadinessCommand(readiness_id=ReadinessId.parse(readiness_id)))
    deleted_id = unwrap_or_400(result)
    return IdResponse(id=str(deleted_id), warnings=result.warnings)
