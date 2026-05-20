"""
Routes pour la gestion des profils utilisateur
"""
from fastapi import APIRouter, HTTPException, Depends
from models.user import UserProfile, UserProfileUpdate
from services.user_service import UserService
from api.dependencies import get_db

router = APIRouter()


@router.get("/{user_id}", response_model=UserProfile)
async def get_user_profile(user_id: int, db=Depends(get_db)):
    """Récupère le profil complet d'un utilisateur."""
    service = UserService(db)
    profile = service.get_profile(user_id)
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profil introuvable")
    
    return profile


@router.put("/{user_id}")
async def update_user_profile(
    user_id: int,
    profile_update: UserProfileUpdate,
    db=Depends(get_db)
):
    """Met à jour le profil d'un utilisateur."""
    service = UserService(db)
    updated = service.update_profile(user_id, profile_update)
    
    return {"message": "Profil mis à jour", "profile": updated}