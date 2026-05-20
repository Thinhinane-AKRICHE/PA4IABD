from sqlalchemy import Column, String, Integer, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class UserProfile(Base):
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, unique=True, nullable=False)
    name = Column(String)
    
    # Préférences voyage
    preferences = Column(JSON)  # {"budget": "moyen", "style": "culturel", "mobilité": "voiture"}
    
    # Contraintes
    dietary_restrictions = Column(JSON)  # ["végétarien", "sans gluten"]
    accessibility_needs = Column(JSON)   # ["fauteuil roulant"]
    
    # Historique
    visited_destinations = Column(JSON)  # ["Paris", "Tokyo", "New York"]
    favorite_activities = Column(JSON)   # ["musées", "randonnée", "gastronomie"]
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)