"""
═══════════════════════════════════════════════════════════════════════
  create_users_table.py — Crée la table 'users' dans Neon Postgres
  
  À lancer UNE FOIS (mais sûr de relancer : IF NOT EXISTS).
═══════════════════════════════════════════════════════════════════════
"""

import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ["NEON_DATABASE_URL"]

# La requête SQL qui crée la table
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id               TEXT PRIMARY KEY,
    nom              TEXT,
    email            TEXT,
    langue           TEXT DEFAULT 'français',
    budget           TEXT,
    type_voyage      TEXT,
    prefs_hotels     TEXT,
    contraintes_alim TEXT,
    destinations_fav TEXT,
    created_at       TIMESTAMP DEFAULT NOW()
);
"""

print("🔌 Connexion à Neon Postgres...")

# 1. On se connecte et on crée la table
with psycopg.connect(DATABASE_URL) as conn:
    with conn.cursor() as cur:
        cur.execute(CREATE_TABLE_SQL)
    conn.commit()

print("✅ Table 'users' créée (ou déjà existante).")

# 2. Vérification : on affiche la structure réelle de la table
#    (ton principe : VÉRIFIER, ne pas supposer 🔬)
with psycopg.connect(DATABASE_URL) as conn:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'users'
            ORDER BY ordinal_position;
        """)
        colonnes = cur.fetchall()

print("\n📋 Structure réelle de la table 'users' :")
for nom_col, type_col in colonnes:
    print(f"   • {nom_col} ({type_col})")