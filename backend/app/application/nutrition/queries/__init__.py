"""Immutable query objects for the Nutrition Application Use Cases."""

from app.application.nutrition.queries.get_nutrition import GetNutritionQuery
from app.application.nutrition.queries.list_nutrition import ListNutritionQuery

__all__ = ["GetNutritionQuery", "ListNutritionQuery"]
