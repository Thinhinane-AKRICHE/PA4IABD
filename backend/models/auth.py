from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt  
import os
from dotenv import load_dotenv

from api.dependencies import get_db_connection

load_dotenv()

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 jours

# Hashage des mots de passe
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


# ============================================
# MODELS
# ============================================

class UserRegister(BaseModel):
    nom: str
    prenom: str
    email: EmailStr
    password: str
    telephone: Optional[str] = None
    date_naissance: Optional[str] = None
    nationalite: Optional[str] = "France"


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    email: str
    nom: str
    prenom: Optional[str] = ""  # ✅ Ajouter le prénom dans la réponse


class UserProfile(BaseModel):
    id: int
    nom: str
    prenom: str
    email: str
    telephone: Optional[str]
    date_naissance: Optional[str]
    nationalite: Optional[str]
    langue_preferee: str


# ============================================
# FONCTIONS UTILITAIRES
# ============================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie si le mot de passe correspond au hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash un mot de passe"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Crée un JWT token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_user_by_email(email: str):
    """Récupère un utilisateur par email"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT id, nom, prenom, email, password_hash, telephone, 
                   date_naissance, nationalite, langue_preferee
            FROM users
            WHERE email = %s
        """, (email,))
        
        user = cur.fetchone()
        
        if user:
            return {
                "id": user[0],
                "nom": user[1],
                "prenom": user[2],
                "email": user[3],
                "password_hash": user[4],
                "telephone": user[5],
                "date_naissance": user[6],
                "nationalite": user[7],
                "langue_preferee": user[8]
            }
        return None
        
    finally:
        cur.close()
        conn.close()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Récupère l'utilisateur courant depuis le token JWT"""
    token = credentials.credentials
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        email: str = payload.get("email")
        
        if user_id is None or email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalide"
            )
        
        return {"user_id": user_id, "email": email}
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide"
        )


# ============================================
# ROUTES
# ============================================

@router.post("/register", response_model=Token)
async def register(user: UserRegister):
    """Inscription d'un nouvel utilisateur"""
    
    # Vérifier si l'email existe déjà
    existing_user = get_user_by_email(user.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cet email est déjà utilisé"
        )
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Hash du mot de passe
        hashed_password = get_password_hash(user.password)
        
        # Créer l'utilisateur
        cur.execute("""
            INSERT INTO users (nom, prenom, email, password_hash, telephone, 
                             date_naissance, nationalite, langue_preferee)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'fr')
            RETURNING id
        """, (
            user.nom,
            user.prenom,
            user.email,
            hashed_password,
            user.telephone,
            user.date_naissance,
            user.nationalite
        ))
        
        user_id = cur.fetchone()[0]
        
        # Créer un profil de voyage par défaut
        cur.execute("""
            INSERT INTO user_travel_profile (
                user_id,
                budget_min_habituel,
                budget_max_habituel,
                types_voyage_preferes,
                centres_interet
            ) VALUES (%s, 50, 150, ARRAY['culturel'], ARRAY['découverte'])
        """, (user_id,))
        
        conn.commit()
        
        # Créer le token JWT
        access_token = create_access_token(
            data={"user_id": user_id, "email": user.email}
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user_id,
            "email": user.email,
            "nom": user.nom,
            "prenom": user.prenom  # ✅ Retourner le prénom
        }
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'inscription: {str(e)}"
        )
    finally:
        cur.close()
        conn.close()


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    """Connexion d'un utilisateur"""
    
    # Récupérer l'utilisateur
    user = get_user_by_email(credentials.email)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect"
        )
    
    # Vérifier le mot de passe
    if not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect"
        )
    
    # Créer le token JWT
    access_token = create_access_token(
        data={"user_id": user["id"], "email": user["email"]}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user["id"],
        "email": user["email"],
        "nom": user["nom"],
        "prenom": user.get("prenom", "")  # ✅ Retourner le prénom
    }


@router.get("/me", response_model=UserProfile)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Récupère le profil de l'utilisateur connecté"""
    
    user = get_user_by_email(current_user["email"])
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )
    
    return {
        "id": user["id"],
        "nom": user["nom"],
        "prenom": user["prenom"],
        "email": user["email"],
        "telephone": user["telephone"],
        "date_naissance": str(user["date_naissance"]) if user["date_naissance"] else None,
        "nationalite": user["nationalite"],
        "langue_preferee": user["langue_preferee"]
    }


@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """
    Déconnexion de l'utilisateur.
    
    Côté serveur, on peut éventuellement blacklister le token,
    mais pour l'instant on laisse le client supprimer le token.
    """
    return {
        "message": "Déconnexion réussie",
        "user_id": current_user["user_id"]
    }