from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from api.dependencies import get_agent
from api.routes.auth import get_current_user  # NOUVEAU

router = APIRouter(prefix="/chat", tags=["Chat"])


class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    thread_id: str
    tools_used: list


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user),  # NOUVEAU : protection JWT
    agent=Depends(get_agent)
):
    
    try:
        user_id = current_user["user_id"]  # NOUVEAU
        
        result = agent.chat(
            message=request.message,
            user_id=user_id,  
            thread_id=request.thread_id
        )
        
        return ChatResponse(
            response=result["response"],
            thread_id=result["thread_id"],
            tools_used=result.get("tools_used", [])
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/new")
async def new_conversation(
    current_user: dict = Depends(get_current_user)  # NOUVEAU
):
    import uuid
    
    user_id = current_user["user_id"]
    thread_id = f"user-{user_id}-{uuid.uuid4().hex[:8]}"
    
    return {
        "thread_id": thread_id,
        "message": "Nouvelle conversation créée"
    }