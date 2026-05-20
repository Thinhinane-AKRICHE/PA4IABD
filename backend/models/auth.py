"""
Modèles d'authentification
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class UserRegister(BaseModel):
    """Inscription utilisateur"""
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8)
    
    model_config = {
        "json_schema_extra": {
            "examples": [{
                "name": "Jean Dupont",
                "email": "jean@example.com",
                "password": "motdepasse123"
            }]
        }
    }


class UserLogin(BaseModel):
    """Connexion utilisateur"""
    email: EmailStr
    password: str
    
    model_config = {
        "json_schema_extra": {
            "examples": [{
                "email": "jean@example.com",
                "password": "motdepasse123"
            }]
        }
    }


class Token(BaseModel):
    """Token JWT"""
    access_token: str
    token_type: str = "bearer"
    user_id: int
    email: str
    name: str


class UserResponse(BaseModel):
    """Réponse utilisateur"""
    id: int
    name: str
    email: str
    
    model_config = {
        "json_schema_extra": {
            "examples": [{
                "id": 1,
                "name": "Jean Dupont",
                "email": "jean@example.com"
            }]
        }
    }