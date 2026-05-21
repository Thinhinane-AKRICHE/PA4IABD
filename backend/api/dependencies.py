"""
Dépendances partagées pour l'API FastAPI et l'agent LangGraph
"""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()


def get_db_connection():
    """
    Crée une connexion à la base de données PostgreSQL.
    Utilisée par :
    - L'API FastAPI (routes auth, chat, user)
    - L'agent LangGraph (pour récupérer le profil utilisateur)
    - Les tools (profile, etc.)
    
    Returns:
        psycopg2.connection: Connexion à la base de données
    """
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        raise ValueError(
            "DATABASE_URL non définie. "
            "Assurez-vous que votre fichier .env contient cette variable."
        )
    
    return psycopg2.connect(database_url)


def get_db():
    """
    Dépendance FastAPI pour injecter une connexion DB dans les routes.
    Utilisé avec Depends(get_db) dans les routes FastAPI.
    
    Yields:
        psycopg2.connection: Connexion qui sera automatiquement fermée après usage
    """
    db = get_db_connection()
    try:
        yield db
    finally:
        db.close()


# ⚠️ IMPORTANT : Import retardé pour éviter l'import circulaire
_agent_instance = None

def get_agent():
    """
    Singleton pour l'agent LangGraph.
    Crée l'agent une seule fois et le réutilise.
    
    Returns:
        TravelBuddyAgent: Instance de l'agent
    """
    global _agent_instance
    
    if _agent_instance is None:
        # Import ICI et non au niveau du module pour éviter l'import circulaire
        from core.agent import TravelBuddyAgent
        _agent_instance = TravelBuddyAgent()
    
    return _agent_instance