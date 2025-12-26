from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.ai.orchestrator import Orchestrator

router = APIRouter()
orchestrator = Orchestrator()

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        if not request.message.strip():
            raise HTTPException(status_code=400, detail="Message tidak boleh kosong")
        
        response = orchestrator.handle_chat(request.message)
        return ChatResponse(response=response)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

