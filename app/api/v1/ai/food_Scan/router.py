from fastapi import APIRouter, Depends
from app.api.deps import verify_token, get_foodscan_service
from app.services.ai_foodscan_orchestrator import AIFoodScanOrchestrator
from .schemas import FoodScanRequest, FoodScanResponse
import json

router = APIRouter(
    dependencies=[Depends(verify_token)]
)

@router.post("/scan", response_model=FoodScanResponse)
async def scan_food(
    req: FoodScanRequest,
    ai: AIFoodScanOrchestrator = Depends(get_foodscan_service)
):
    result = await ai.scan_food(image_url=req.image_url)
    
    # Parse JSON string to dict
    result_dict = json.loads(result)
    
    return result_dict
