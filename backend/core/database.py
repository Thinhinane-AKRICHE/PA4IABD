"""
database.py - Gestion de la base de données Travel Buddy
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, ARRAY, DECIMAL, Boolean, DateTime, Text, JSON, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

load_dotenv()
DATABASE_URL = os.environ["DATABASE_URL"]

# Configuration optimisée pour Neon
engine = create_engine(
    DATABASE_URL, 
    echo=False,
    connect_args={
        "sslmode": "require",
        "connect_timeout": 10,
    }
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency pour obtenir une session DB"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)  # Pour l'authentification
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)  # Nouveau champ pour auth
    
    # Champs du profil utilisateur existant
    nom = Column(String(255))
    prenom = Column(String(255))
    telephone = Column(String(50))
    date_naissance = Column(Date)
    nationalite = Column(String(100))
    langue_preferee = Column(String(10), default='fr')
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserTravelProfile(Base):
    __tablename__ = "user_travel_profile"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True, nullable=False)
    
    budget_min_habituel = Column(Integer)
    budget_max_habituel = Column(Integer)
    devise_preferee = Column(String(3), default='EUR')
    
    types_voyage_preferes = Column(ARRAY(Text))
    rythme_prefere = Column(String(50))
    duree_voyage_typique = Column(Integer)
    periodes_preferees = Column(ARRAY(Text))
    
    regime_alimentaire = Column(ARRAY(Text))
    allergies_alimentaires = Column(ARRAY(Text))
    cuisines_preferees = Column(ARRAY(Text))
    
    categories_hotel_preferees = Column(ARRAY(Text))
    etoiles_min_preferees = Column(Integer)
    etoiles_max_preferees = Column(Integer)
    prefere_centre_ville = Column(Boolean, default=True)
    prefere_calme = Column(Boolean, default=False)
    prefere_proche_transport = Column(Boolean, default=True)
    types_logement_acceptes = Column(ARRAY(Text))
    equipements_essentiels = Column(ARRAY(Text))
    equipements_souhaites = Column(ARRAY(Text))
    exige_annulation_gratuite = Column(Boolean, default=True)
    accepte_paiement_sur_place = Column(Boolean, default=True)
    
    modes_transport_preferes = Column(ARRAY(Text))
    classe_vol_preferee = Column(String(50))
    accepte_escales = Column(Boolean, default=True)
    
    voyage_generalement_avec = Column(ARRAY(Text))
    nombre_enfants = Column(Integer, default=0)
    ages_enfants = Column(ARRAY(Integer))
    contraintes_mobilite = Column(ARRAY(Text))
    
    climats_preferes = Column(ARRAY(Text))
    types_destinations_preferees = Column(ARRAY(Text))
    
    centres_interet = Column(ARRAY(Text))
    problemes_sante = Column(ARRAY(Text))
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class FavoriteDestination(Base):
    __tablename__ = "user_favorite_destinations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    pays = Column(String(255), nullable=False)
    ville = Column(String(255))
    raison = Column(Text)
    note = Column(Integer)
    deja_visite = Column(Boolean, default=False)
    aimerait_revisiter = Column(Boolean, default=False)
    added_at = Column(DateTime, default=datetime.utcnow)


class BlacklistDestination(Base):
    __tablename__ = "user_blacklist_destinations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    pays = Column(String(255), nullable=False)
    ville = Column(String(255))
    raison = Column(Text)
    added_at = Column(DateTime, default=datetime.utcnow)


def create_tables():
    """Crée toutes les tables dans Neon PostgreSQL"""
    try:
        print("🔄 Création des tables dans Neon PostgreSQL...")
        Base.metadata.create_all(bind=engine)
        print("✅ Tables créées avec succès!")
    except Exception as e:
        print(f"❌ Erreur lors de la création des tables: {e}")
        raise


def create_test_user():
    """Crée un utilisateur de test"""
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == "marie.dubois@example.com").first()
        if existing:
            print(f"Utilisateur test existe déjà (ID: {existing.id})")
            return existing.id
        
        # Note: Pour créer un vrai utilisateur avec mot de passe, utilisez l'endpoint /register
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        user = User(
            name="Marie Dubois",
            email="marie.dubois@example.com",
            hashed_password=pwd_context.hash("password123"),  # Mot de passe de test
            nom="Dubois",
            prenom="Marie",
            langue_preferee="fr",
            nationalite="France"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        profile = UserTravelProfile(
            user_id=user.id,
            budget_min_habituel=800,
            budget_max_habituel=2500,
            devise_preferee="EUR",
            types_voyage_preferes=['culturel', 'gastronomique', 'detente'],
            rythme_prefere='equilibre',
            regime_alimentaire=['vegetarien'],
            categories_hotel_preferees=['boutique', 'confort'],
            etoiles_min_preferees=3,
            etoiles_max_preferees=4,
            equipements_essentiels=['wifi', 'petit_dejeuner_inclus', 'climatisation'],
            equipements_souhaites=['piscine', 'spa'],
            prefere_centre_ville=True,
            exige_annulation_gratuite=True,
            climats_preferes=['tempere', 'chaud'],
            centres_interet=['musees', 'architecture', 'gastronomie', 'photographie']
        )
        db.add(profile)
        
        fav1 = FavoriteDestination(user_id=user.id, pays='Japon', ville='Tokyo', note=5, deja_visite=False)
        fav2 = FavoriteDestination(user_id=user.id, pays='Italie', ville='Florence', note=5, deja_visite=True)
        db.add(fav1)
        db.add(fav2)
        
        blacklist = BlacklistDestination(user_id=user.id, pays='Arabie Saoudite', raison='Contraintes trop strictes')
        db.add(blacklist)
        
        db.commit()
        print(f"Utilisateur test créé avec profil complet (ID: {user.id})")
        print(f"   Email: marie.dubois@example.com")
        print(f"   Mot de passe: password123")
        return user.id
        
    finally:
        db.close()


if __name__ == "__main__":
    print("=== Initialisation de la base de données Travel Buddy ===\n")
    create_tables()
    print()
    user_id = create_test_user()