from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import chat
from api.routes import auth

app = FastAPI(title="TravelBuddy API")

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
    return {"message": "TravelBuddy API"}

# ✅ CORRECTION : Ajouter /api au début
@app.get("/api/health")
def health_check():
    return {"status": "online", "message": "API opérationnelle"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)