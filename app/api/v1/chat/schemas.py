from pydantic import BaseModel
from typing import List, Optional


class ChatHistory(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: List[ChatHistory] = []
    image_url: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
