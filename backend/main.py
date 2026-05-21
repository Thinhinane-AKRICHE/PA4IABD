from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from api.routes import chat, auth
from api.dependencies import init_db_pool, close_db_pool, get_db_connection, get_pool_stats

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gère le cycle de vie de l'application"""
    # ========== STARTUP ==========
    logger.info("=" * 60)
    logger.info("Démarrage de l'application TravelBuddy")
    logger.info("=" * 60)
    
    try:
        init_db_pool()
        logger.info("Application prête")
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation du pool: {e}")
        raise
    
    yield
    
    # ========== SHUTDOWN ==========
    logger.info("=" * 60)
    logger.info("Arrêt de l'application TravelBuddy")
    logger.info("=" * 60)
    close_db_pool()
    logger.info("Application arrêtée proprement")


# Création de l'app avec lifespan
app = FastAPI(
    title="TravelBuddy API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes AVEC le préfixe /api
app.include_router(auth.router, prefix="/api")  
app.include_router(chat.router, prefix="/api")  


@app.get("/")
def read_root():
    return {"message": "TravelBuddy API - Votre compagnon de voyage intelligent"}


@app.get("/api/health")
def health_check():
    """Vérifie la santé de l'API et de la base de données"""
    try:
        # Test de connexion à la DB
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        
        # Récupère les stats du pool
        pool_stats = get_pool_stats()
        
        return {
            "status": "healthy",
            "message": "API opérationnelle",
            "database": "connected",
            "pool": pool_stats
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "message": "Problème détecté",
            "database": "disconnected",
            "error": str(e)
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_level="info"
    )