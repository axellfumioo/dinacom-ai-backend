from fastapi import APIRouter
from app.api.v1.chat.router import router as chat_router
from fastapi import FastAPI
from datetime import datetime
api_router = APIRouter()

api_router.include_router(chat_router, prefix="/ai", tags=["AI Chat"])
@api_router.get("/ping", tags=["Utility"])
async def ping():
    return {
        "status": "success",
        "message": "pong",
        "date": datetime.utcnow().isoformat()
    }