"""Handlers for the Nutrition Application Use Cases. See
`docs/adr/0025-nutrition-application-use-cases.md`.
"""

from app.application.nutrition.handlers.delete_nutrition_handler import DeleteNutritionHandler
from app.application.nutrition.handlers.get_nutrition_handler import GetNutritionHandler
from app.application.nutrition.handlers.list_nutrition_handler import ListNutritionHandler
from app.application.nutrition.handlers.record_nutrition_handler import RecordNutritionHandler
from app.application.nutrition.handlers.update_notes_handler import UpdateNutritionNotesHandler
from app.application.nutrition.handlers.update_nutrition_handler import UpdateNutritionHandler
from app.application.nutrition.handlers.update_water_handler import UpdateWaterHandler

__all__ = [
    "DeleteNutritionHandler",
    "GetNutritionHandler",
    "ListNutritionHandler",
    "RecordNutritionHandler",
    "UpdateNutritionHandler",
    "UpdateNutritionNotesHandler",
    "UpdateWaterHandler",
]
