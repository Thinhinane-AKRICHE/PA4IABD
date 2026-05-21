"""
Modèles Pydantic pour les requêtes/réponses du chat
"""
from pydantic import BaseModel, Field
from typing import Optional, List


class ChatRequest(BaseModel):
    """
    Requête pour envoyer un message à l'agent.
    Le user_id est extrait automatiquement du JWT token, pas de la requête.
    """
    message: str = Field(..., description="Message de l'utilisateur")
    thread_id: Optional[str] = Field(None, description="ID de la conversation (optionnel)")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "message": "Je cherche un hôtel à Paris",
                    "thread_id": None
                }
            ]
        }
    }


class ChatResponse(BaseModel):
    """
    Réponse de l'agent.
    """
    response: str = Field(..., description="Réponse générée par l'agent")
    thread_id: str = Field(..., description="ID de la conversation")
    tools_used: List[str] = Field(default_factory=list, description="Liste des outils utilisés par l'agent")
    user_id: int = Field(..., description="ID de l'utilisateur (pour information)")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "response": "Voici quelques suggestions d'hôtels à Paris adaptées à votre budget...",
                    "thread_id": "user-1-abc123",
                    "tools_used": ["search_destination_info", "get_hotels_info"],
                    "user_id": 1
                }
            ]
        }
    }


class NewConversationResponse(BaseModel):
    """
    Réponse lors de la création d'une nouvelle conversation.
    """
    thread_id: str = Field(..., description="ID de la nouvelle conversation")
    message: str = Field(..., description="Message de confirmation")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "thread_id": "user-1-def456",
                    "message": "Nouvelle conversation créée"
                }
            ]
        }
    }