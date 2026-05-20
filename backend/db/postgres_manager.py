"""
Gestionnaire centralisé pour Neon Postgres.
Gère à la fois la mémoire LangGraph ET les données métier.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from .models import Base, UserProfile, SavedItinerary, WeatherCache, QueryLog
from datetime import datetime, timedelta

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL, pool_size=10, max_overflow=20)
SessionLocal = sessionmaker(bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)
    print("Tables Postgres créées (ou déjà existantes)")


@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_user_profile(user_id: str):
    with get_db() as db:
        profile = db.query(UserProfile).filter_by(user_id=user_id).first()
        if not profile:
            profile = UserProfile(user_id=user_id, preferences={})
            db.add(profile)
            db.commit()
        return profile


def save_itinerary(user_id: str, destination: str, title: str, data: dict):
    with get_db() as db:
        itinerary = SavedItinerary(
            user_id=user_id,
            destination=destination,
            title=title,
            itinerary_data=data
        )
        db.add(itinerary)
        db.commit()
        return itinerary.id


def get_cached_weather(city: str, max_age_hours: int = 1):
    with get_db() as db:
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        cache = db.query(WeatherCache).filter(
            WeatherCache.city == city,
            WeatherCache.fetched_at >= cutoff
        ).first()
        
        return cache.data if cache else None


def cache_weather(city: str, data: dict):
    with get_db() as db:
        cache = WeatherCache(city=city, data=data)
        db.add(cache)
        db.commit()