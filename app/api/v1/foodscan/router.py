from fastapi import APIRouter, HTTPException, Depends
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from typing import Any, Dict
from app.ai.orchestrator import Orchestrator
from app.dependency.deps import verify_token
from openai import APITimeoutError
import traceback


router = APIRouter()
orchestrator = Orchestrator()

class ChatRequest(BaseModel):
    image_url: str

class ChatResponse(BaseModel):
    response: Dict[str, Any]

@router.post("/foodscan", response_model=ChatResponse)
async def chat(request: ChatRequest, _: bool = Depends(verify_token)):
    try:
        if not request.image_url.strip():
            raise HTTPException(status_code=400, detail="image_url tidak boleh kosong")
        
        response = await run_in_threadpool(orchestrator.handle_scan, request.image_url)
        return ChatResponse(response=response)

    except APITimeoutError:
        raise HTTPException(
            status_code=504,
            detail="LLM request timed out. Increase OPENAI_TIMEOUT_S (and optionally OPENAI_MAX_RETRIES).",
        )
    
    except Exception as e:
        print(f"ERROR in chat endpoint: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

