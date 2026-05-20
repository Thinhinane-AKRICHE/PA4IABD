from pydantic import BaseModel
from typing import Optional


class ChatRequest(BaseModel):
    message: str
    provider: str = "openai"
    model: str = "gpt-4.1-nano"
    temperature: float = 0
    thread_id: str = "default-thread"
    user_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    provider: str
    model: str