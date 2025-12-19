from pydantic import BaseModel
from typing import Optional


class FoodScanRequest(BaseModel):
    image_url: str


class FoodScanResponse(BaseModel):
    food_name: str
    calories: float
    protein: float
    carbohydrates: float
    fat: float
    ingredients: list[str]
    description: str
