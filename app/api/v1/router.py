from fastapi import APIRouter
from app.api.v1.ai.chat.router import router as chat_router
from app.api.v1.ai.food_scan.router import router as food_scan_router
from fastapi import FastAPI
from datetime import datetime
api_router = APIRouter()

api_router.include_router(chat_router, prefix="/ai", tags=["AI Chat"])
api_router.include_router(food_scan_router, prefix="/ai/food", tags=["AI Food Scan"])
@api_router.get("/ping", tags=["Utility"])
async def ping():
    return {
        "status": "success",
        "message": "pong",
        "date": datetime.utcnow().isoformat()
    }