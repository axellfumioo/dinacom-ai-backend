from fastapi import Header, HTTPException, status
from app.core.config import settings
from app.services.vision_service import VisionService
from app.services.llm_service import LLMService
from app.services.ai_chat_orchestrator import AIOrchestrator
from app.services.ai_foodscan_orchestrator import AIFoodScanOrchestrator

def get_ai_service():
    return AIOrchestrator(
        vision=VisionService(),
        llm=LLMService()
    )

def get_foodscan_service():
    return AIFoodScanOrchestrator()

def verify_token(authorization: str = Header(...)):
    """
    Expect:
    Authorization: Bearer <TOKEN>
    """

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization format"
        )

    token = authorization.replace("Bearer ", "")

    if token != settings.secret_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    return True
