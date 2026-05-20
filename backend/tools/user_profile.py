"""
═══════════════════════════════════════════════════════════════════════
  user_profile.py — Sauvegarde et chargement des profils utilisateurs
  
  Couche FONCTIONS : parle directement à la table 'users' de Neon.
  • save_user_profile(...)  → crée OU met à jour un profil (UPSERT)
  • load_user_profile(id)   → récupère un profil (dict) ou None
═══════════════════════════════════════════════════════════════════════
"""

import os
import psycopg
from psycopg.rows import dict_row   # → curseur qui renvoie des dictionnaires
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ["NEON_DATABASE_URL"]


def save_user_profile(
    user_id: str,
    nom: str = "",
    email: str = "",
    langue: str = "français",
    budget: str = "",
    type_voyage: str = "",
    prefs_hotels: str = "",
    contraintes_alim: str = "",
    destinations_fav: str = "",
) -> bool:
    """
    Crée un nouveau profil, OU met à jour s'il existe déjà (UPSERT).
    Retourne True si OK, False si erreur.
    """
    
    # 🔒 SÉCURITÉ : %s (placeholders), JAMAIS de f-string dans le SQL
    sql = """
        INSERT INTO users (
            id, nom, email, langue, budget,
            type_voyage, prefs_hotels, contraintes_alim, destinations_fav
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET
            nom              = EXCLUDED.nom,
            email            = EXCLUDED.email,
            langue           = EXCLUDED.langue,
            budget           = EXCLUDED.budget,
            type_voyage      = EXCLUDED.type_voyage,
            prefs_hotels     = EXCLUDED.prefs_hotels,
            contraintes_alim = EXCLUDED.contraintes_alim,
            destinations_fav = EXCLUDED.destinations_fav;
    """
    
    try:
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (
                    user_id, nom, email, langue, budget,
                    type_voyage, prefs_hotels, contraintes_alim, destinations_fav
                ))
            conn.commit()
        return True
    
    except Exception as e:
        print(f"❌ Erreur save_user_profile : {e}")
        return False


def load_user_profile(user_id: str):
    """
    Récupère le profil d'un utilisateur par son id.
    Retourne un dict {colonne: valeur}, ou None si introuvable.
    """
    
    sql = "SELECT * FROM users WHERE id = %s;"
    
    try:
        # row_factory=dict_row → chaque ligne est un dict, pas un tuple
        with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (user_id,))
                profil = cur.fetchone()   # 1 seule ligne (id = clé primaire)
        
        return profil   # dict ou None
    
    except Exception as e:
        print(f"❌ Erreur load_user_profile : {e}")
        return None


# ═══════════════════════════════════════════════════════════════════════
# 🧪 TEST STANDALONE
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("🧪 Test de user_profile.py\n")
    print("=" * 60)
    
    # 1. On crée (ou met à jour) un utilisateur de test
    print("💾 Sauvegarde d'un profil test...")
    ok = save_user_profile(
        user_id="user_001",
        nom="Sirine",
        email="sirine@example.com",
        langue="français",
        budget="500 euros",
        type_voyage="culturel",
        prefs_hotels="économique, proche centre",
        contraintes_alim="végétarienne",
        destinations_fav="Marrakech, Lyon, Venise",
    )
    print(f"   → Sauvegarde réussie : {ok}")
    
    # 2. On le recharge depuis Neon (preuve de persistance)
    print("\n📥 Chargement du profil 'user_001'...")
    profil = load_user_profile("user_001")
    
    if profil:
        print("   → Profil trouvé :")
        for cle, valeur in profil.items():
            print(f"      {cle} : {valeur}")
    else:
        print("   → Aucun profil trouvé.")
    
    # 3. Test : utilisateur inexistant (graceful)
    print("\n📥 Chargement d'un id inexistant...")
    vide = load_user_profile("user_999")
    print(f"   → Résultat : {vide}")
    
    print("=" * 60)