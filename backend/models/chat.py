"""
Modèles Pydantic pour les requêtes/réponses du chat
"""
from pydantic import BaseModel, Field
from typing import Optional, List


class ChatRequest(BaseModel):
    """
    Requête pour envoyer un message à l'agent.
    """
    message: str = Field(..., description="Message de l'utilisateur")
    user_id: int = Field(default=1, description="ID de l'utilisateur")
    thread_id: Optional[str] = Field(None, description="ID de la conversation")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "message": "Je cherche un hôtel à Paris",
                    "user_id": 1,
                    "thread_id": None
                }
            ]
        }
    }


class ChatResponse(BaseModel):
    """
    Réponse de l'agent.
    """
    response: str = Field(..., description="Réponse de l'agent")
    user_id: int = Field(..., description="ID de l'utilisateur")
    thread_id: str = Field(..., description="ID de la conversation")
    tools_used: List[str] = Field(default_factory=list, description="Outils utilisés par l'agent")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "response": "Voici quelques suggestions d'hôtels à Paris...",
                    "user_id": 1,
                    "thread_id": "user-1-abc123",
                    "tools_used": ["search_destination_info", "get_profile_info"]
                }
            ]
        }
    }