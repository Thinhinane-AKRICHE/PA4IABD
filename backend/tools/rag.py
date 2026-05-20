"""
RAG Tool de Travel Buddy.

Tool principal: search_rag(destination, query)
→ Cherche dans Wikivoyage pour n'importe quelle ville.
→ Auto-ingère la ville si elle n'est pas déjà en base.
"""

import os
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from utils.wikivoyage_loader import fetch_wikivoyage
import chromadb


# ============================================================
# SETUP (s'exécute à l'import du module)
# ============================================================
load_dotenv()

# Initialisation OpenAI
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Chemin ChromaDB (compatible Docker)
CHROMA_PATH = os.getenv("CHROMA_PERSIST_DIR", "/app/chroma_db")
Path(CHROMA_PATH).mkdir(parents=True, exist_ok=True)

# Initialisation ChromaDB avec gestion d'erreur
try:
    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = chroma_client.get_or_create_collection(
        name="travel_chunks",
        metadata={"hnsw:space": "cosine"}
    )
    print(f"✓ ChromaDB initialisé : {collection.count()} chunks en base")
except Exception as e:
    print(f"⚠️  Erreur ChromaDB : {e}")
    # Fallback : créer un nouveau client
    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = chroma_client.get_or_create_collection(
        name="travel_chunks",
        metadata={"hnsw:space": "cosine"}
    )


# ============================================================
# FONCTIONS UTILITAIRES
# ============================================================

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list:
    """
    Découpe un texte en chunks avec overlap pour préserver le contexte.
    
    Args:
        text: Le texte à découper
        chunk_size: Taille cible de chaque chunk (en caractères)
        overlap: Nombre de caractères qui se chevauchent entre chunks consécutifs
    
    Returns:
        Liste de chunks (strings)
    """
    words = text.split()
    chunks = []
    current_chunk = []
    current_size = 0
    
    for word in words:
        # Si on dépasse la taille cible → on ferme le chunk actuel
        if current_size + len(word) > chunk_size:
            # 1. Sauvegarder le chunk actuel
            chunks.append(" ".join(current_chunk))
            
            # 2. PRÉPARER L'OVERLAP : garder les DERNIERS mots du chunk précédent
            overlap_words = []
            overlap_size = 0
            
            # On parcourt le chunk précédent à L'ENVERS
            for w in reversed(current_chunk):
                if overlap_size + len(w) > overlap:
                    break
                overlap_words.insert(0, w)  # Insérer au début (ordre normal)
                overlap_size += len(w) + 1
            
            # 3. Le nouveau chunk commence avec ces mots + le mot actuel
            current_chunk = overlap_words + [word]
            current_size = overlap_size + len(word)
        else:
            # Cas normal : on ajoute le mot au chunk actuel
            current_chunk.append(word)
            current_size += len(word) + 1
    
    # Ne pas oublier le dernier chunk
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    
    return chunks


def is_destination_indexed(destination: str) -> bool:
    """Vérifie si la destination existe déjà dans la base."""
    try:
        results = collection.get(where={"destination": destination}, limit=1)
        return len(results["ids"]) > 0
    except Exception as e:
        print(f"⚠️  Erreur vérification index : {e}")
        return False


def ingest_destination(destination: str) -> int:
    """Télécharge, chunke, embed et stocke une destination. Retourne le nb de chunks."""
    print(f"\n🔄 Ingestion de {destination}...")
    
    try:
        # 1. Télécharger depuis Wikivoyage
        text = fetch_wikivoyage(destination)
        
        # 2. Chunker
        chunks = chunk_text(text, chunk_size=500)
        print(f"   ✂️  {len(chunks)} chunks créés")
        
        # 3. Embedder TOUS les chunks en UN SEUL appel (batch = rapide + moins cher)
        print(f"   🔢 Création des embeddings...")
        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=chunks
        )
        embeddings = [item.embedding for item in response.data]
        
        # 4. Supprimer les anciens chunks de cette destination (au cas où re-ingestion)
        existing = collection.get(where={"destination": destination})
        if existing["ids"]:
            collection.delete(ids=existing["ids"])
        
        # 5. Stocker dans ChromaDB
        collection.add(
            ids=[f"{destination}_{i}" for i in range(len(chunks))],
            documents=chunks,
            embeddings=embeddings,
            metadatas=[{"destination": destination} for _ in chunks]
        )
        
        print(f"   ✅ {len(chunks)} chunks stockés pour {destination}")
        return len(chunks)
        
    except Exception as e:
        print(f"   ❌ Erreur ingestion : {e}")
        return 0


# ============================================================
# LE TOOL — search_rag
# ============================================================

def search_rag(destination: str, query: str, n_results: int = 3) -> dict:
    """
    LE TOOL principal de Travel Buddy.
    Cherche les chunks Wikivoyage les plus pertinents pour une question.
    Auto-ingère la destination si elle n'est pas déjà en base.
    
    Returns:
        dict avec structure compatible avec l'agent
    """
    try:
        # AUTO-INGESTION si nouvelle destination
        if not is_destination_indexed(destination):
            print(f"⚠️  {destination} n'est pas en base. Ingestion automatique...")
            ingest_destination(destination)
        
        # Embedder la query
        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=query
        )
        query_embedding = response.data[0].embedding
        
        # Chercher dans ChromaDB
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where={"destination": destination}
        )
        
        # Retourner au format attendu par l'agent
        if results and "documents" in results and results["documents"]:
            return {
                "documents": results["documents"],
                "error": None
            }
        else:
            return {
                "documents": [[f"Aucune information trouvée pour {destination}"]],
                "error": "no_results"
            }
            
    except Exception as e:
        print(f"❌ Erreur search_rag : {e}")
        return {
            "documents": [[f"Erreur lors de la recherche : {str(e)}"]],
            "error": str(e)
        }


# ============================================================
# TEST (s'exécute si on lance ce fichier)
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("🚀 TEST RAG COMPLET — Multi-destinations")
    print("=" * 60)
    
    # Pré-ingestion des 3 villes principales (skip si déjà fait)
    villes_principales = ["Paris", "Tokyo", "New York"]
    
    for ville in villes_principales:
        if is_destination_indexed(ville):
            print(f"\n✓ {ville} déjà en base")
        else:
            ingest_destination(ville)
    
    print(f"\n📊 Total dans la collection : {collection.count()} chunks")
    
    # Tests de recherche
    print("\n" + "=" * 60)
    print("🔍 TESTS DE RECHERCHE PAR VILLE")
    print("=" * 60)
    
    tests = [
        ("Paris", "Quels musées historiques visiter ?"),
        ("Tokyo", "Quelles spécialités culinaires goûter ?"),
        ("New York", "Quels quartiers iconiques voir ?"),
    ]
    
    for ville, query in tests:
        print(f"\n❓ [{ville}] {query}")
        result = search_rag(ville, query, n_results=2)
        chunks = result.get("documents", [[]])[0]
        for i, chunk in enumerate(chunks, 1):
            apercu = chunk.replace("\n", " ")[:130]
            print(f"   {i}. {apercu}...")
    
    # TEST FINAL : une nouvelle ville (auto-ingestion)
    print("\n" + "=" * 60)
    print("🆕 TEST AUTO-INGESTION — Nouvelle ville (Bangkok)")
    print("=" * 60)
    
    result = search_rag("Bangkok", "Que voir dans la ville ?", n_results=2)
    chunks = result.get("documents", [[]])[0]
    print(f"\n❓ [Bangkok] Que voir dans la ville ?")
    for i, chunk in enumerate(chunks, 1):
        apercu = chunk.replace("\n", " ")[:130]
        print(f"   {i}. {apercu}...")
    
    print(f"\nTotal final : {collection.count()} chunks dans la base")
    print("\nTool search_rag fonctionnel pour TOUTES LES VILLES DU MONDE !")