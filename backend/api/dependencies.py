import os
from dotenv import load_dotenv
import psycopg2
from core.agent import TravelBuddyAgent

load_dotenv()

# Instance globale de l'agent
_agent_instance = None


def get_agent():
    """Dépendance FastAPI pour obtenir l'instance de l'agent"""
    global _agent_instance
    
    if _agent_instance is None:
        _agent_instance = TravelBuddyAgent()
    
    return _agent_instance


def get_db_connection():
    """
    Crée et retourne une connexion à la base de données PostgreSQL.
    
    Returns:
        psycopg2.connection: Connexion à la base de données
    """
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        raise ValueError("DATABASE_URL non définie dans les variables d'environnement")
    
    try:
        conn = psycopg2.connect(database_url)
        return conn
    except Exception as e:
        raise Exception(f"Erreur de connexion à la base de données : {str(e)}")