"""
Dépendances partagées pour l'API FastAPI et l'agent LangGraph
"""
import os
from psycopg_pool import ConnectionPool
from contextlib import contextmanager
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

# ============================================
# POOL DE CONNEXIONS GLOBAL
# ============================================

_connection_pool = None


def init_db_pool():
    """
    Initialise le pool de connexions PostgreSQL au démarrage de l'application.
    À appeler une seule fois dans le lifespan de FastAPI.
    
    Returns:
        ConnectionPool: Instance du pool de connexions
    """
    global _connection_pool
    
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        raise ValueError(
            "DATABASE_URL non définie. "
            "Assurez-vous que votre fichier .env contient cette variable."
        )
    
    if _connection_pool is not None:
        logger.warning("Pool de connexions déjà initialisé")
        return _connection_pool
    
    logger.info("🔌 Initialisation du pool de connexions PostgreSQL...")
    
    _connection_pool = ConnectionPool(
        conninfo=database_url,
        min_size=2,          # Minimum 2 connexions toujours ouvertes
        max_size=10,         # Maximum 10 connexions simultanées
        timeout=30,          # Timeout d'attente pour obtenir une connexion
        max_idle=300,        # Fermer les connexions inactives après 5 min
        max_lifetime=3600,   # Recycler les connexions après 1 heure
        kwargs={
            "connect_timeout": 10,
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 5,
        }
    )
    
    logger.info("Pool de connexions initialisé avec succès")
    return _connection_pool


def close_db_pool():
    """
    Ferme le pool de connexions.
    À appeler lors de l'arrêt de l'application (shutdown event).
    """
    global _connection_pool
    
    if _connection_pool:
        logger.info("Fermeture du pool de connexions...")
        _connection_pool.close()
        _connection_pool = None
        logger.info("Pool de connexions fermé")


def get_pool():
    """
    Retourne l'instance du pool de connexions.
    Lève une erreur si le pool n'est pas initialisé.
    
    Returns:
        ConnectionPool: Pool de connexions
    """
    if _connection_pool is None:
        raise RuntimeError(
            "Le pool de connexions n'est pas initialisé. "
            "Appelez init_db_pool() au démarrage de l'application."
        )
    return _connection_pool


# ============================================
# FONCTIONS DE CONNEXION (pour compatibilité)
# ============================================

@contextmanager
def get_db_connection():
    """
    Context manager pour obtenir une connexion du pool.
    Gère automatiquement commit/rollback et retour au pool.
    
    Utilisée par :
    - L'API FastAPI (routes auth, chat, user)
    - L'agent LangGraph (pour récupérer le profil utilisateur)
    - Les tools (profile, etc.)
    
    Usage:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM users")
                
    Yields:
        psycopg.Connection: Connexion à la base de données
    """
    pool = get_pool()
    conn = pool.getconn()
    
    try:
        yield conn
        # Commit automatique si pas d'erreur
        conn.commit()
    except Exception as e:
        # Rollback en cas d'erreur
        conn.rollback()
        logger.error(f"Erreur base de données, rollback effectué: {e}")
        raise
    finally:
        # Retourne la connexion au pool
        pool.putconn(conn)


def get_db():
    """
    Dépendance FastAPI pour injecter une connexion DB dans les routes.
    Utilisé avec Depends(get_db) dans les routes FastAPI.
    
    Usage:
        @router.get("/users")
        async def get_users(db = Depends(get_db)):
            with db.cursor() as cur:
                cur.execute("SELECT * FROM users")
    
    Yields:
        psycopg.Connection: Connexion qui sera automatiquement retournée au pool
    """
    pool = get_pool()
    conn = pool.getconn()
    
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Erreur base de données dans route FastAPI: {e}")
        raise
    finally:
        pool.putconn(conn)


# ============================================
# SINGLETON AGENT
# ============================================

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
        logger.info("Initialisation de l'agent TravelBuddy...")
        _agent_instance = TravelBuddyAgent()
        logger.info("Agent initialisé")
    
    return _agent_instance


# ============================================
# UTILITAIRES DE DIAGNOSTIC
# ============================================

def get_pool_stats():
    """
    Retourne les statistiques du pool de connexions.
    Utile pour le monitoring et le debugging.
    
    Returns:
        dict: Statistiques du pool
    """
    if _connection_pool is None:
        return {"error": "Pool non initialisé"}
    
    return {
        "size": _connection_pool._pool.qsize() if hasattr(_connection_pool, '_pool') else "N/A",
        "min_size": _connection_pool.min_size,
        "max_size": _connection_pool.max_size,
        "timeout": _connection_pool.timeout,
    }