"""HTTP routes for the Progress module — seven endpoints, one per
Application Handler in `app.application.progress.handlers`. See
`goal.py`'s module docstring for what every route here does and does
not do.

| Method | Path                                          | Handler                     |
|--------|-----------------------------------------------|-------------------------------|
| POST   | /api/v1/progress                              | RecordProgressHandler          |
| GET    | /api/v1/progress/{progress_id}                | GetProgressHandler             |
| GET    | /api/v1/progress                              | ListProgressHandler            |
| PUT    | /api/v1/progress/{progress_id}/body-composition | UpdateBodyCompositionHandler |
| PUT    | /api/v1/progress/{progress_id}/measurements   | UpdateMeasurementsHandler       |
| PUT    | /api/v1/progress/{progress_id}/notes          | UpdateNotesHandler              |
| DELETE | /api/v1/progress/{progress_id}                | DeleteProgressHandler           |
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.deps import handler_dependency
from app.api.errors import unwrap_or_400, unwrap_or_404, unwrap_or_500
from app.api.schemas.common import IdResponse
from app.api.schemas.progress import (
    ProgressResponse,
    RecordProgressRequest,
    UpdateBodyCompositionRequest,
    UpdateMeasurementsRequest,
    UpdateProgressNotesRequest,
)
from app.application.progress.commands.delete_progress import DeleteProgressCommand
from app.application.progress.handlers.delete_progress_handler import DeleteProgressHandler
from app.application.progress.handlers.get_progress_handler import GetProgressHandler
from app.application.progress.handlers.list_progress_handler import ListProgressHandler
from app.application.progress.handlers.record_progress_handler import RecordProgressHandler
from app.application.progress.handlers.update_body_composition_handler import (
    UpdateBodyCompositionHandler,
)
from app.application.progress.handlers.update_measurements_handler import (
    UpdateMeasurementsHandler,
)
from app.application.progress.handlers.update_notes_handler import UpdateNotesHandler
from app.application.progress.queries.get_progress import GetProgressQuery
from app.application.progress.queries.list_progress import ListProgressQuery
from app.domain.progress.identifiers import ProgressId
from app.domain.user.identifiers import UserId

router = APIRouter(prefix="/progress", tags=["progress"])

_get_record_handler = handler_dependency(RecordProgressHandler)
_get_get_handler = handler_dependency(GetProgressHandler)
_get_list_handler = handler_dependency(ListProgressHandler)
_get_update_body_composition_handler = handler_dependency(UpdateBodyCompositionHandler)
_get_update_measurements_handler = handler_dependency(UpdateMeasurementsHandler)
_get_update_notes_handler = handler_dependency(UpdateNotesHandler)
_get_delete_handler = handler_dependency(DeleteProgressHandler)


@router.post("", response_model=IdResponse, status_code=status.HTTP_201_CREATED)
def record_progress(
    body: RecordProgressRequest, handler: RecordProgressHandler = Depends(_get_record_handler)
) -> IdResponse:
    result = handler.handle(body.to_command())
    progress_id = unwrap_or_400(result)
    return IdResponse(id=str(progress_id), warnings=result.warnings)


@router.get("/{progress_id}", response_model=ProgressResponse)
def get_progress(
    progress_id: str, handler: GetProgressHandler = Depends(_get_get_handler)
) -> ProgressResponse:
    result = handler.handle(GetProgressQuery(progress_id=ProgressId.parse(progress_id)))
    return ProgressResponse.from_dto(unwrap_or_404(result))


@router.get("", response_model=list[ProgressResponse])
def list_progress(
    user_id: str, handler: ListProgressHandler = Depends(_get_list_handler)
) -> list[ProgressResponse]:
    result = handler.handle(ListProgressQuery(user_id=UserId.parse(user_id)))
    return [ProgressResponse.from_dto(dto) for dto in unwrap_or_500(result)]


@router.put("/{progress_id}/body-composition", response_model=IdResponse)
def update_body_composition(
    progress_id: str,
    body: UpdateBodyCompositionRequest,
    handler: UpdateBodyCompositionHandler = Depends(_get_update_body_composition_handler),
) -> IdResponse:
    result = handler.handle(body.to_command(ProgressId.parse(progress_id)))
    updated_id = unwrap_or_400(result)
    return IdResponse(id=str(updated_id), warnings=result.warnings)


@router.put("/{progress_id}/measurements", response_model=IdResponse)
def update_measurements(
    progress_id: str,
    body: UpdateMeasurementsRequest,
    handler: UpdateMeasurementsHandler = Depends(_get_update_measurements_handler),
) -> IdResponse:
    result = handler.handle(body.to_command(ProgressId.parse(progress_id)))
    updated_id = unwrap_or_400(result)
    return IdResponse(id=str(updated_id), warnings=result.warnings)


@router.put("/{progress_id}/notes", response_model=IdResponse)
def update_progress_notes(
    progress_id: str,
    body: UpdateProgressNotesRequest,
    handler: UpdateNotesHandler = Depends(_get_update_notes_handler),
) -> IdResponse:
    result = handler.handle(body.to_command(ProgressId.parse(progress_id)))
    updated_id = unwrap_or_400(result)
    return IdResponse(id=str(updated_id), warnings=result.warnings)


@router.delete("/{progress_id}", response_model=IdResponse)
def delete_progress(
    progress_id: str, handler: DeleteProgressHandler = Depends(_get_delete_handler)
) -> IdResponse:
    result = handler.handle(DeleteProgressCommand(progress_id=ProgressId.parse(progress_id)))
    deleted_id = unwrap_or_400(result)
    return IdResponse(id=str(deleted_id), warnings=result.warnings)
