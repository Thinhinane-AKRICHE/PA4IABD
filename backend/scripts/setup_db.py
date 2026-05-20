"""
Initialise la base Postgres avec toutes les tables.
À lancer une seule fois au démarrage du projet.
"""

from backend.db.postgres_manager import init_db

if __name__ == "__main__":
    print("Initialisation de la base Neon Postgres...")
    init_db()
    print("Base prete")