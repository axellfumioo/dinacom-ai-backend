from fastapi import APIRouter, HTTPException, Depends
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from typing import List, Dict, Optional
from app.ai.orchestrator import Orchestrator
from app.dependency.deps import verify_token
import traceback

router = APIRouter()
orchestrator = Orchestrator()

class ChatRequest(BaseModel):
    message: str
    chat_history: Optional[List[Dict[str, str]]] = None

class ChatResponse(BaseModel):
    response: str

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, _: bool = Depends(verify_token)):
    try:
        if not request.message.strip():
            raise HTTPException(status_code=400, detail="Message tidak boleh kosong")
        
        # Orchestrator uses sync network I/O (OpenAI, requests); run it off the event loop.
        response = await run_in_threadpool(orchestrator.handle_chat, request.message, request.chat_history)
        return ChatResponse(response=response)
    
    except Exception as e:
        print(f"ERROR in chat endpoint: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

