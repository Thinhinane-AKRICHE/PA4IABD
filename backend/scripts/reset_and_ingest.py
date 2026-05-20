"""
reset_and_ingest.py

Script utilitaire pour :
1. Supprimer l'ancienne base ChromaDB
2. Ré-ingérer les villes principales avec le NOUVEAU chunking (overlap)

À lancer une seule fois après modification de chunk_text.
"""

import shutil
import os

# ════════════════════════════════════════
# ÉTAPE 1 : SUPPRIMER l'ancienne base
# ════════════════════════════════════════
# Important : on supprime AVANT d'importer rag,
# car rag.py initialise ChromaDB à l'import.

print("=" * 50)
print("🗑️  ÉTAPE 1 : Suppression de l'ancienne base")
print("=" * 50)

if os.path.exists("./chroma_db"):
    shutil.rmtree("./chroma_db", ignore_errors=True)
    print("✅ Dossier chroma_db/ supprimé.\n")
else:
    print("ℹ️  Pas de dossier chroma_db/ à supprimer.\n")


# ════════════════════════════════════════
# ÉTAPE 2 : RÉ-INGÉRER les villes principales
# ════════════════════════════════════════
# On importe MAINTENANT (après la suppression),
# pour que rag.py recrée une base FRAÎCHE.

print("=" * 50)
print("📦 ÉTAPE 2 : Initialisation de la nouvelle base")
print("=" * 50)

from rag import ingest_destination

print("✅ Nouvelle base initialisée.\n")

# Liste des villes à ré-ingérer
villes_a_ingerer = ["Paris", "Tokyo", "New York"]

print("=" * 50)
print(f"🌍 ÉTAPE 3 : Ré-ingestion de {len(villes_a_ingerer)} villes")
print("=" * 50)
print()

for i, ville in enumerate(villes_a_ingerer, 1):
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"🚀 [{i}/{len(villes_a_ingerer)}] Ingestion de {ville}...")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━")
    ingest_destination(ville)
    print()


# ════════════════════════════════════════
# FIN
# ════════════════════════════════════════
print("=" * 50)
print("✨ RÉINITIALISATION TERMINÉE !")
print("=" * 50)
print()
print("✅ Les 3 villes principales sont ré-indexées avec overlap.")
print("✅ Les autres villes (Alger, Bangkok, etc.) seront")
print("   automatiquement ré-ingérées à la prochaine recherche.")
print()