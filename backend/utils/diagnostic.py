"""
diagnostic.py — Affiche le contenu de ChromaDB
Détecte automatiquement toutes les collections.
"""

import chromadb

# Connexion à ta base ChromaDB
client = chromadb.PersistentClient(path="./chroma_db")

# 🔍 LISTE TOUTES les collections (sans deviner les noms)
collections = client.list_collections()

print(f"📊 Collections trouvées : {len(collections)}")
print("=" * 60)

if len(collections) == 0:
    print("⚠️  Aucune collection trouvée. Ta base est vide.")
else:
    for col in collections:
        print(f"\n🗂️  Collection : '{col.name}'")
        print(f"   📈 Nombre de chunks : {col.count()}")
        
        if col.count() > 0:
            # Récupère TOUT le contenu pour analyser
            data = col.get(include=["metadatas"])
            
            # Extrait les villes uniques depuis les metadata
            villes = set()
            for m in data["metadatas"]:
                if m and "destination" in m:
                    villes.add(m["destination"])
            
            if villes:
                print(f"   🏙️  Villes indexées ({len(villes)}) :")
                for v in sorted(villes):
                    # Compte les chunks par ville
                    chunks_ville = sum(1 for m in data["metadatas"] 
                                       if m and m.get("destination") == v)
                    print(f"      • {v} ({chunks_ville} chunks)")
            else:
                print("   ℹ️  Pas de metadata 'destination' (autre structure)")
                # Affiche la 1ère metadata pour comprendre la structure
                if data["metadatas"]:
                    print(f"   🔬 Exemple metadata : {data['metadatas'][0]}")

print()
print("=" * 60)