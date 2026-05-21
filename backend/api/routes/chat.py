"""
Routes pour le chat avec l'agent IA
"""
from fastapi import APIRouter, HTTPException, Depends

from models.chat import ChatRequest, ChatResponse, NewConversationResponse
from api.dependencies import get_agent
from api.routes.auth import get_current_user

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user),  # 🔒 JWT validation
    agent=Depends(get_agent)
):
    """
    Endpoint principal pour discuter avec l'agent IA.
    
    **Authentification requise** : Le token JWT doit être fourni dans le header Authorization.
    
    Le profil utilisateur est chargé automatiquement par l'agent pour personnaliser
    les recommandations selon :
    - Budget habituel
    - Centres d'intérêt
    - Régime alimentaire
    - Préférences d'hébergement
    - Destinations favorites/blacklist
    
    Args:
        request: Message et thread_id optionnel
        current_user: Utilisateur extrait du JWT (automatique)
        agent: Instance de l'agent LangGraph (singleton)
    
    Returns:
        ChatResponse: Réponse de l'IA avec thread_id et tools utilisés
        
    Raises:
        HTTPException 401: Si le token JWT est invalide ou manquant
        HTTPException 500: Si l'agent rencontre une erreur
    """
    
    try:
        # Extraire le user_id du JWT
        user_id = current_user["user_id"]
        
        # L'agent charge AUTOMATIQUEMENT le profil et génère la réponse
        result = agent.chat(
            message=request.message,
            user_id=user_id,
            thread_id=request.thread_id
        )
        
        return ChatResponse(
            response=result["response"],
            thread_id=result["thread_id"],
            tools_used=result.get("tools_used", []),
            user_id=user_id
        )
        
    except Exception as e:
        print(f"❌ Erreur dans /chat/: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur lors du traitement du message: {str(e)}"
        )


@router.post("/new", response_model=NewConversationResponse)
async def new_conversation(
    current_user: dict = Depends(get_current_user)
):
    """
    Crée une nouvelle conversation.
    
    **Authentification requise**
    
    Returns:
        NewConversationResponse: Nouveau thread_id unique pour la conversation
        
    Raises:
        HTTPException 401: Si le token JWT est invalide ou manquant
    """
    import uuid
    
    user_id = current_user["user_id"]
    thread_id = f"user-{user_id}-{uuid.uuid4().hex[:8]}"
    
    return NewConversationResponse(
        thread_id=thread_id,
        message="Nouvelle conversation créée"
    )


@router.get("/history/{thread_id}")
async def get_conversation_history(
    thread_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Récupère l'historique d'une conversation.
    
    **Authentification requise**
    
    Vérifie que la conversation appartient bien à l'utilisateur connecté.
    
    Args:
        thread_id: ID de la conversation
        current_user: Utilisateur connecté
    
    Returns:
        dict: Historique de la conversation
        
    Raises:
        HTTPException 401: Si le token JWT est invalide
        HTTPException 403: Si la conversation n'appartient pas à l'utilisateur
    """
    user_id = current_user["user_id"]
    
    # Vérifier que le thread appartient bien à cet utilisateur
    if not thread_id.startswith(f"user-{user_id}-"):
        raise HTTPException(
            status_code=403, 
            detail="Accès refusé : cette conversation ne vous appartient pas"
        )
    
    # TODO: Implémenter la récupération de l'historique depuis PostgreSQL
    # Pour l'instant, retourner un placeholder
    return {
        "thread_id": thread_id,
        "user_id": user_id,
        "messages": [],
        "message": "Historique non encore implémenté"
    }