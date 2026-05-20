"""
Tool get_user_profile — Récupère le profil utilisateur pour personnaliser les suggestions.

Ce tool permet à l'agent d'accéder aux préférences permanentes de l'utilisateur :
- Budget habituel
- Régime alimentaire (végétarien, allergies, etc.)
- Préférences hôtels (étoiles, équipements ESSENTIELS)
- Centres d'intérêt
- Destinations favorites et blacklist

L'agent DOIT utiliser ce profil pour filtrer et adapter toutes ses suggestions.
"""

import os
import sys
from pathlib import Path

# Ajouter le dossier parent au path pour importer database
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.database import UserTravelProfile, FavoriteDestination, BlacklistDestination

load_dotenv()

# Configuration DB
DATABASE_URL = os.environ.get("DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ============================================================
# TOOL PRINCIPAL
# ============================================================

def get_user_profile(user_id: int = None) -> dict:
    """
    Récupère le profil complet de l'utilisateur.
    
    Args:
        user_id: ID de l'utilisateur (par défaut 1)
    
    Returns:
        Dict structuré avec toutes les préférences, ou erreur si user introuvable
    """
    
    if user_id is None:
        user_id = 1
    
    db = SessionLocal()
    
    try:
        # Récupérer le profil de voyage
        profile = db.query(UserTravelProfile).filter(
            UserTravelProfile.user_id == user_id
        ).first()
        
        if not profile:
            return {
                "error": f"Aucun profil trouvé pour l'utilisateur {user_id}",
                "suggestion": "L'utilisateur doit créer son profil de voyage"
            }
        
        # Récupérer les destinations favorites
        favorites = db.query(FavoriteDestination).filter(
            FavoriteDestination.user_id == user_id
        ).all()
        
        # Récupérer la blacklist
        blacklist = db.query(BlacklistDestination).filter(
            BlacklistDestination.user_id == user_id
        ).all()
        
        return {
            "user_id": user_id,
            "budget": {
                "min": profile.budget_min_habituel,
                "max": profile.budget_max_habituel,
                "devise": profile.devise_preferee
            },
            "voyage": {
                "types_preferes": profile.types_voyage_preferes or [],
                "rythme": profile.rythme_prefere,
                "duree_typique_jours": profile.duree_voyage_typique,
                "periodes_preferees": profile.periodes_preferees or [],
                "voyage_avec": profile.voyage_generalement_avec or []
            },
            "alimentation": {
                "regime": profile.regime_alimentaire or [],
                "allergies": profile.allergies_alimentaires or [],
                "cuisines_preferees": profile.cuisines_preferees or []
            },
            "hotels": {
                "categories_preferees": profile.categories_hotel_preferees or [],
                "etoiles_min": profile.etoiles_min_preferees,
                "etoiles_max": profile.etoiles_max_preferees,
                "localisation": {
                    "centre_ville": profile.prefere_centre_ville,
                    "calme": profile.prefere_calme,
                    "proche_transport": profile.prefere_proche_transport
                },
                "types_acceptes": profile.types_logement_acceptes or [],
                "equipements_essentiels": profile.equipements_essentiels or [],
                "equipements_souhaites": profile.equipements_souhaites or [],
                "annulation_gratuite": profile.exige_annulation_gratuite,
                "paiement_sur_place": profile.accepte_paiement_sur_place
            },
            "transport": {
                "modes_preferes": profile.modes_transport_preferes or [],
                "classe_vol": profile.classe_vol_preferee,
                "accepte_escales": profile.accepte_escales
            },
            "contexte": {
                "nombre_enfants": profile.nombre_enfants,
                "ages_enfants": profile.ages_enfants or [],
                "contraintes_mobilite": profile.contraintes_mobilite or []
            },
            "preferences_destination": {
                "climats_preferes": profile.climats_preferes or [],
                "types_destinations": profile.types_destinations_preferees or []
            },
            "interets": profile.centres_interet or [],
            "sante": {
                "problemes": profile.problemes_sante or []
            },
            "destinations": {
                "favorites": [
                    {
                        "pays": fav.pays,
                        "ville": fav.ville,
                        "raison": fav.raison,
                        "note": fav.note,
                        "deja_visite": fav.deja_visite,
                        "voudrait_revisiter": fav.aimerait_revisiter
                    }
                    for fav in favorites
                ],
                "blacklist": [
                    {
                        "pays": bl.pays,
                        "ville": bl.ville,
                        "raison": bl.raison
                    }
                    for bl in blacklist
                ]
            }
        }
    
    except Exception as e:
        return {
            "error": f"Erreur lors de la récupération du profil : {str(e)}"
        }
    
    finally:
        db.close()


def format_profile_for_agent(profile: dict) -> str:
    if "error" in profile:
        return f"Erreur: {profile['error']}"
    
    text = f"""
PROFIL UTILISATEUR (ID: {profile['user_id']})
{'=' * 60}

BUDGET HABITUEL
   Range : {profile['budget']['min']}€ - {profile['budget']['max']}€
   Devise : {profile['budget']['devise']}

ALIMENTATION
   Regime : {', '.join(profile['alimentation']['regime']) if profile['alimentation']['regime'] else 'Aucun'}
   Allergies : {', '.join(profile['alimentation']['allergies']) if profile['alimentation']['allergies'] else 'Aucune'}
   Cuisines preferees : {', '.join(profile['alimentation']['cuisines_preferees']) if profile['alimentation']['cuisines_preferees'] else 'Non specifie'}

PREFERENCES HOTELS
   Categories : {', '.join(profile['hotels']['categories_preferees']) if profile['hotels']['categories_preferees'] else 'Non specifie'}
   Etoiles : {profile['hotels']['etoiles_min']} - {profile['hotels']['etoiles_max']}
   Localisation : {'Centre-ville' if profile['hotels']['localisation']['centre_ville'] else 'Excentre'}, {'Calme' if profile['hotels']['localisation']['calme'] else 'Anime'}
   
   EQUIPEMENTS ESSENTIELS (BLOQUANTS) :
   {chr(10).join(f'   - {equip}' for equip in profile['hotels']['equipements_essentiels'])}
   
   Equipements souhaites (bonus) :
   {chr(10).join(f'   - {equip}' for equip in profile['hotels']['equipements_souhaites'])}
   
   Annulation gratuite requise : {'Oui' if profile['hotels']['annulation_gratuite'] else 'Non'}

CENTRES D'INTERET
   {', '.join(profile['interets']) if profile['interets'] else 'Non specifie'}

PREFERENCES DESTINATIONS
   Climats preferes : {', '.join(profile['preferences_destination']['climats_preferes']) if profile['preferences_destination']['climats_preferes'] else 'Non specifie'}
   Types : {', '.join(profile['preferences_destination']['types_destinations']) if profile['preferences_destination']['types_destinations'] else 'Non specifie'}

DESTINATIONS FAVORITES ({len(profile['destinations']['favorites'])})
"""
    
    if profile['destinations']['favorites']:
        for fav in profile['destinations']['favorites']:
            status = "Visite" if fav['deja_visite'] else "Wishlist"
            ville = f", {fav['ville']}" if fav['ville'] else ""
            text += f"   - {fav['pays']}{ville} ({fav['note']}/5) {status}\n"
    
    if profile['destinations']['blacklist']:
        text += f"\nDESTINATIONS A EVITER ({len(profile['destinations']['blacklist'])})\n"
        for bl in profile['destinations']['blacklist']:
            ville = f", {bl['ville']}" if bl['ville'] else ""
            text += f"   - {bl['pays']}{ville} - {bl['raison']}\n"
    
    text += "\n" + "=" * 60
    text += """

REGLES POUR L'AGENT :
1. Les EQUIPEMENTS ESSENTIELS sont BLOQUANTS - Ne JAMAIS suggerer un hotel qui n'a pas ces equipements
2. Respecter le regime alimentaire pour TOUS les restaurants
3. Adapter les suggestions aux centres d'interet
4. Ne JAMAIS suggerer les destinations en blacklist
5. Privilegier les destinations favorites ou similaires
"""
    
    return text


if __name__ == "__main__":
    profile = get_user_profile(user_id=1)
    print(format_profile_for_agent(profile))