"""
Module pour récupérer et formater le profil utilisateur depuis la base de données.
"""

import os
import json
import psycopg2
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()


def get_db_connection():
    """
    Crée une connexion à la base de données PostgreSQL.
    
    Returns:
        psycopg2.connection: Connexion à la base de données
    """
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        raise ValueError("DATABASE_URL non définie dans les variables d'environnement")
    
    try:
        conn = psycopg2.connect(
            database_url,
            connect_timeout=10,
            sslmode='require',
            keepalives=1,
            keepalives_idle=30,
            keepalives_interval=10,
            keepalives_count=5
        )
        return conn
    except Exception as e:
        print(f"Erreur connexion DB: {e}")
        raise


def get_user_profile(user_id: int) -> Dict[str, Any]:
    """
    Récupère le profil complet d'un utilisateur depuis la base de données.
    
    Args:
        user_id: ID de l'utilisateur
        
    Returns:
        Dict contenant toutes les informations du profil utilisateur
    """
    
    conn = None
    cur = None
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                id, nom, prenom, email, nationalite, langue_preferee
            FROM users
            WHERE id = %s
        """, (user_id,))
        
        user = cur.fetchone()
        
        if not user:
            return {"error": f"Utilisateur {user_id} non trouvé"}
        
        cur.execute("""
            SELECT 
                budget_min_habituel,
                budget_max_habituel,
                devise_preferee,
                types_voyage_preferes,
                rythme_prefere,
                duree_voyage_typique,
                periodes_preferees,
                regime_alimentaire,
                allergies_alimentaires,
                cuisines_preferees,
                categories_hotel_preferees,
                etoiles_min_preferees,
                etoiles_max_preferees,
                prefere_centre_ville,
                prefere_calme,
                prefere_proche_transport,
                types_logement_acceptes,
                equipements_essentiels,
                equipements_souhaites,
                exige_annulation_gratuite,
                accepte_paiement_sur_place,
                modes_transport_preferes,
                classe_vol_preferee,
                accepte_escales,
                voyage_generalement_avec,
                nombre_enfants,
                ages_enfants,
                contraintes_mobilite,
                climats_preferes,
                types_destinations_preferees,
                centres_interet,
                problemes_sante
            FROM user_travel_profile
            WHERE user_id = %s
        """, (user_id,))
        
        profile = cur.fetchone()
        
        cur.execute("""
            SELECT pays, ville, raison, note, deja_visite, aimerait_revisiter
            FROM user_favorite_destinations
            WHERE user_id = %s
            ORDER BY note DESC
        """, (user_id,))
        
        favorites_rows = cur.fetchall()
        
        cur.execute("""
            SELECT pays, ville, raison
            FROM user_blacklist_destinations
            WHERE user_id = %s
        """, (user_id,))
        
        blacklist_rows = cur.fetchall()
        
        result = {
            "user_id": user[0],
            "nom": user[1],
            "prenom": user[2],
            "email": user[3],
            "nationalite": user[4],
            "langue_preferee": user[5],
        }
        
        if profile:
            result.update({
                "budget_min": profile[0],
                "budget_max": profile[1],
                "devise_preferee": profile[2],
                "types_voyage_preferes": profile[3] or [],
                "rythme_prefere": profile[4],
                "duree_voyage_typique": profile[5],
                "periodes_preferees": profile[6] or [],
                "regime_alimentaire": profile[7],
                "allergies_alimentaires": profile[8] or [],
                "cuisines_preferees": profile[9] or [],
                "categories_hotel_preferees": profile[10] or [],
                "etoiles_min_preferees": profile[11],
                "etoiles_max_preferees": profile[12],
                "prefere_centre_ville": profile[13],
                "prefere_calme": profile[14],
                "prefere_proche_transport": profile[15],
                "types_logement_acceptes": profile[16] or [],
                "equipements_essentiels": profile[17] or [],
                "equipements_souhaites": profile[18] or [],
                "exige_annulation_gratuite": profile[19],
                "accepte_paiement_sur_place": profile[20],
                "modes_transport_preferes": profile[21] or [],
                "classe_vol_preferee": profile[22],
                "accepte_escales": profile[23],
                "voyage_generalement_avec": profile[24] or [],
                "nombre_enfants": profile[25],
                "ages_enfants": profile[26] or [],
                "contraintes_mobilite": profile[27] or [],
                "climats_preferes": profile[28] or [],
                "types_destinations_preferees": profile[29] or [],
                "centres_interet": profile[30] or [],
                "problemes_sante": profile[31] or [],
            })
        
        result["destinations_favorites"] = [
            {
                "pays": row[0],
                "ville": row[1],
                "raison": row[2],
                "note": row[3],
                "deja_visite": row[4],
                "aimerait_revisiter": row[5]
            }
            for row in favorites_rows
        ]
        
        result["destinations_blacklist"] = [
            {
                "pays": row[0],
                "ville": row[1],
                "raison": row[2]
            }
            for row in blacklist_rows
        ]
        
        return result
        
    except Exception as e:
        print(f"Erreur get_user_profile: {e}")
        return {"error": f"Erreur lors de la récupération du profil : {str(e)}"}
    
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def format_profile_for_agent(profile: Dict[str, Any]) -> str:
    """
    Formate le profil utilisateur au format JSON structuré pour le LLM.
    
    Args:
        profile: Dictionnaire contenant le profil utilisateur complet
        
    Returns:
        str: Profil au format JSON structuré et lisible pour le LLM
    """
    
    if "error" in profile:
        return ""
    
    clean_profile = {}
    
    if profile.get('prenom'):
        clean_profile['prenom'] = profile['prenom']
    if profile.get('nom'):
        clean_profile['nom'] = profile['nom']
    if profile.get('nationalite'):
        clean_profile['nationalite'] = profile['nationalite']
    
    if profile.get('budget_min') or profile.get('budget_max'):
        budget_info = {}
        if profile.get('budget_min'):
            budget_info['min_par_jour'] = profile['budget_min']
        if profile.get('budget_max'):
            budget_info['max_par_jour'] = profile['budget_max']
        budget_info['devise'] = profile.get('devise_preferee', 'EUR')
        clean_profile['budget'] = budget_info
    
    if profile.get('types_voyage_preferes'):
        clean_profile['types_voyage'] = profile['types_voyage_preferes']
    
    if profile.get('rythme_prefere'):
        clean_profile['rythme'] = profile['rythme_prefere']
    
    if profile.get('centres_interet'):
        clean_profile['centres_interet'] = profile['centres_interet']
    
    if profile.get('destinations_favorites'):
        clean_profile['destinations_favorites'] = [
            {
                'pays': f['pays'],
                'ville': f.get('ville'),
                'raison': f.get('raison'),
                'note': f.get('note')
            }
            for f in profile['destinations_favorites']
        ]
    
    if profile.get('destinations_blacklist'):
        clean_profile['destinations_a_eviter'] = [
            {
                'pays': b['pays'],
                'raison': b.get('raison')
            }
            for b in profile['destinations_blacklist']
        ]
    
    if profile.get('regime_alimentaire'):
        regime = profile['regime_alimentaire']
        clean_profile['regime_alimentaire'] = regime if isinstance(regime, list) else [regime]
    
    if profile.get('allergies_alimentaires'):
        clean_profile['allergies'] = profile['allergies_alimentaires']
    
    if profile.get('cuisines_preferees'):
        clean_profile['cuisines_preferees'] = profile['cuisines_preferees']
    
    hebergement = {}
    
    if profile.get('etoiles_min_preferees'):
        hebergement['etoiles_min'] = profile['etoiles_min_preferees']
    if profile.get('etoiles_max_preferees'):
        hebergement['etoiles_max'] = profile['etoiles_max_preferees']
    
    if profile.get('categories_hotel_preferees'):
        hebergement['categories'] = profile['categories_hotel_preferees']
    
    if profile.get('equipements_essentiels'):
        hebergement['equipements_essentiels'] = profile['equipements_essentiels']
    
    if hebergement:
        clean_profile['hebergement'] = hebergement
    
    if profile.get('modes_transport_preferes'):
        clean_profile['transports'] = profile['modes_transport_preferes']
    
    if profile.get('contraintes_mobilite'):
        clean_profile['contraintes_mobilite'] = profile['contraintes_mobilite']
    
    return json.dumps(clean_profile, ensure_ascii=False, indent=2)