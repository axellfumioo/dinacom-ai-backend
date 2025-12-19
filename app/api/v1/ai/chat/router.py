from fastapi import APIRouter, Depends
from app.api.deps import verify_token, get_ai_service
from app.services.ai_chat_orchestrator import AIOrchestrator
from .schemas import ChatRequest, ChatResponse

router = APIRouter(
    dependencies=[Depends(verify_token)]
)

@router.post("/chat", response_model=ChatResponse)
async def chat(
    req: ChatRequest,
    ai: AIOrchestrator = Depends(get_ai_service)
):
    reply = await ai.chat(
        message=req.message,
        history=[m.dict() for m in req.history],
        image_url=req.image_url
    )

    return {"reply": reply}
