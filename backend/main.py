# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Travel Assistant API",
    description="AI-powered travel planning assistant",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "message": "Travel Assistant API v1.0",
        "status": "running"
    }

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/test-db")
def test_db():
    """Test connexion à PostgreSQL"""
    from sqlalchemy import create_engine, text
    
    try:
        DATABASE_URL = os.getenv("DATABASE_URL")
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as connection:
            result = connection.execute(text("SELECT COUNT(*) FROM users"))
            count = result.scalar()
        
        return {
            "database": "connected",
            "users_count": count
        }
    except Exception as e:
        return {
            "database": "error",
            "error": str(e)
        }

@app.get("/test-redis")
def test_redis():
    """Test connexion à Redis"""
    import redis
    
    try:
        REDIS_URL = os.getenv("REDIS_URL")
        r = redis.from_url(REDIS_URL)
        r.ping()
        
        return {
            "redis": "connected"
        }
    except Exception as e:
        return {
            "redis": "error",
            "error": str(e)
        }