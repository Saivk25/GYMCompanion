"""HTTP routes for the Nutrition module — seven endpoints, one per
Application Handler in `app.application.nutrition.handlers`. See
`goal.py`'s module docstring for what every route here does and does
not do.

| Method | Path                                | Handler                    |
|--------|-------------------------------------|-----------------------------|
| POST   | /api/v1/nutrition                   | RecordNutritionHandler       |
| GET    | /api/v1/nutrition/{nutrition_id}    | GetNutritionHandler          |
| GET    | /api/v1/nutrition                   | ListNutritionHandler         |
| PATCH  | /api/v1/nutrition/{nutrition_id}    | UpdateNutritionHandler       |
| PUT    | /api/v1/nutrition/{nutrition_id}/water | UpdateWaterHandler        |
| PUT    | /api/v1/nutrition/{nutrition_id}/notes | UpdateNutritionNotesHandler |
| DELETE | /api/v1/nutrition/{nutrition_id}    | DeleteNutritionHandler       |
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.deps import get_current_user_id, handler_dependency
from app.api.errors import unwrap_or_400, unwrap_or_404, unwrap_or_500
from app.api.schemas.common import IdResponse
from app.api.schemas.nutrition import (
    NutritionResponse,
    RecordNutritionRequest,
    UpdateNutritionNotesRequest,
    UpdateNutritionRequest,
    UpdateWaterRequest,
)
from app.application.nutrition.commands.delete_nutrition import DeleteNutritionCommand
from app.application.nutrition.handlers.delete_nutrition_handler import DeleteNutritionHandler
from app.application.nutrition.handlers.get_nutrition_handler import GetNutritionHandler
from app.application.nutrition.handlers.list_nutrition_handler import ListNutritionHandler
from app.application.nutrition.handlers.record_nutrition_handler import RecordNutritionHandler
from app.application.nutrition.handlers.update_notes_handler import UpdateNutritionNotesHandler
from app.application.nutrition.handlers.update_nutrition_handler import UpdateNutritionHandler
from app.application.nutrition.handlers.update_water_handler import UpdateWaterHandler
from app.application.nutrition.queries.get_nutrition import GetNutritionQuery
from app.application.nutrition.queries.list_nutrition import ListNutritionQuery
from app.domain.nutrition.identifiers import NutritionId
from app.domain.user.identifiers import UserId

router = APIRouter(prefix="/nutrition", tags=["nutrition"])

_get_record_handler = handler_dependency(RecordNutritionHandler)
_get_get_handler = handler_dependency(GetNutritionHandler)
_get_list_handler = handler_dependency(ListNutritionHandler)
_get_update_handler = handler_dependency(UpdateNutritionHandler)
_get_update_water_handler = handler_dependency(UpdateWaterHandler)
_get_update_notes_handler = handler_dependency(UpdateNutritionNotesHandler)
_get_delete_handler = handler_dependency(DeleteNutritionHandler)


@router.post("", response_model=IdResponse, status_code=status.HTTP_201_CREATED)
def record_nutrition(
    body: RecordNutritionRequest,
    user_id: UserId = Depends(get_current_user_id),
    handler: RecordNutritionHandler = Depends(_get_record_handler),
) -> IdResponse:
    result = handler.handle(body.to_command(user_id))
    nutrition_id = unwrap_or_400(result)
    return IdResponse(id=str(nutrition_id), warnings=result.warnings)


@router.get("/{nutrition_id}", response_model=NutritionResponse)
def get_nutrition(
    nutrition_id: str,
    _user_id: UserId = Depends(get_current_user_id),
    handler: GetNutritionHandler = Depends(_get_get_handler),
) -> NutritionResponse:
    result = handler.handle(GetNutritionQuery(nutrition_id=NutritionId.parse(nutrition_id)))
    return NutritionResponse.from_dto(unwrap_or_404(result))


@router.get("", response_model=list[NutritionResponse])
def list_nutrition(
    user_id: UserId = Depends(get_current_user_id),
    handler: ListNutritionHandler = Depends(_get_list_handler),
) -> list[NutritionResponse]:
    result = handler.handle(ListNutritionQuery(user_id=user_id))
    return [NutritionResponse.from_dto(dto) for dto in unwrap_or_500(result)]


@router.patch("/{nutrition_id}", response_model=IdResponse)
def update_nutrition(
    nutrition_id: str,
    body: UpdateNutritionRequest,
    _user_id: UserId = Depends(get_current_user_id),
    handler: UpdateNutritionHandler = Depends(_get_update_handler),
) -> IdResponse:
    result = handler.handle(body.to_command(NutritionId.parse(nutrition_id)))
    updated_id = unwrap_or_400(result)
    return IdResponse(id=str(updated_id), warnings=result.warnings)


@router.put("/{nutrition_id}/water", response_model=IdResponse)
def update_water(
    nutrition_id: str,
    body: UpdateWaterRequest,
    _user_id: UserId = Depends(get_current_user_id),
    handler: UpdateWaterHandler = Depends(_get_update_water_handler),
) -> IdResponse:
    result = handler.handle(body.to_command(NutritionId.parse(nutrition_id)))
    updated_id = unwrap_or_400(result)
    return IdResponse(id=str(updated_id), warnings=result.warnings)


@router.put("/{nutrition_id}/notes", response_model=IdResponse)
def update_nutrition_notes(
    nutrition_id: str,
    body: UpdateNutritionNotesRequest,
    _user_id: UserId = Depends(get_current_user_id),
    handler: UpdateNutritionNotesHandler = Depends(_get_update_notes_handler),
) -> IdResponse:
    result = handler.handle(body.to_command(NutritionId.parse(nutrition_id)))
    updated_id = unwrap_or_400(result)
    return IdResponse(id=str(updated_id), warnings=result.warnings)


@router.delete("/{nutrition_id}", response_model=IdResponse)
def delete_nutrition(
    nutrition_id: str,
    _user_id: UserId = Depends(get_current_user_id),
    handler: DeleteNutritionHandler = Depends(_get_delete_handler),
) -> IdResponse:
    result = handler.handle(DeleteNutritionCommand(nutrition_id=NutritionId.parse(nutrition_id)))
    deleted_id = unwrap_or_400(result)
    return IdResponse(id=str(deleted_id), warnings=result.warnings)
