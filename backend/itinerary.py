"""
═══════════════════════════════════════════════════════════════════════
  itinerary.py — Génère un programme de voyage structuré
  
  🆕 Option 2 : ANCRÉ dans le RAG (Wikivoyage)
     Pattern RAG classique : Récupérer → Augmenter → Générer
═══════════════════════════════════════════════════════════════════════
"""

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# 🆕 On importe NOTRE RAG pour ancrer l'itinéraire dans Wikivoyage
from rag import search_rag

load_dotenv()

# LLM dédié à la structuration de l'itinéraire
_llm = ChatOpenAI(model="gpt-4.1-nano", temperature=0.4)


def _get_wikivoyage_context(destination: str, interests: str = "") -> str:
    """
    ① RÉCUPÉRER : va chercher les vraies infos Wikivoyage via le RAG.
    Réutilise la même logique robuste que dans agent.py.
    Retourne une chaîne, ou "" si rien trouvé (→ graceful degradation).
    """
    # La requête RAG est ciblée selon les centres d'intérêt
    query = f"{interests} visiter activités restaurants que faire".strip()
    
    try:
        results = search_rag(destination, query)
        
        if isinstance(results, dict):
            if "documents" in results and results["documents"]:
                chunks = results["documents"][0][:10]
                return "\n\n---\n\n".join(chunks)
            if "error" in results:
                return ""
        
        if isinstance(results, list):
            return "\n\n---\n\n".join(results[:10])
        
        return str(results)
    
    except Exception:
        return ""


def generate_itinerary(
    destination: str,
    days: int = 3,
    interests: str = "",
    budget: str = "",
) -> str:
    """
    Génère un programme de voyage structuré jour par jour,
    ANCRÉ dans les vraies données Wikivoyage (RAG-augmented).
    
    Args:
        destination: Ville (ex: 'Lyon', 'Venise')
        days: Nombre de jours
        interests: Centres d'intérêt (ex: 'gastronomie')
        budget: Budget indicatif (ex: '800 euros')
    """
    
    # ① RÉCUPÉRER les vraies infos Wikivoyage
    contexte = _get_wikivoyage_context(destination, interests)
    
    # ② Choisir l'instruction selon qu'on a des données… ou pas
    if contexte:
        source_instruction = f"""Voici des informations RÉELLES issues de Wikivoyage 
sur {destination}. Tu DOIS baser ton programme sur CES informations :

--- INFOS WIKIVOYAGE ---
{contexte}
--- FIN INFOS ---

Utilise EN PRIORITÉ les lieux, quartiers et conseils ci-dessus.
"""
    else:
        # Graceful degradation : pas de données RAG → on reste honnête
        source_instruction = f"""Aucune donnée Wikivoyage spécifique trouvée pour 
{destination}. Génère un programme plausible depuis tes connaissances, 
mais reste prudent et général.
"""
    
    # ③ AUGMENTER le prompt + GÉNÉRER
    prompt = f"""Génère un programme de voyage détaillé et structuré.

Destination : {destination}
Durée : {days} jours
Centres d'intérêt : {interests if interests else "découverte générale"}
Budget indicatif : {budget if budget else "non précisé"}

{source_instruction}

RÈGLES DE FORMAT (à respecter STRICTEMENT) :
- Un titre pour chaque journée : "JOUR 1 : <thème>", etc.
- Pour chaque journée, EXACTEMENT 4 lignes :
  • Matin : <activité>
  • Après-midi : <activité>
  • Soir : <activité>
  • Repas conseillé : <suggestion>
- Termine par une section "BUDGET ESTIMÉ" avec une ventilation
  (hébergement, repas, activités, transport).
- Si un budget est donné, vérifie que le total reste cohérent avec lui.
- N'invente JAMAIS de prix précis d'hôtels : reste en fourchettes,
  et précise que les prix exacts sont à vérifier en ligne.
- Réponds en français, clair et structuré.
"""

    try:
        response = _llm.invoke(prompt)
        return response.content
    except Exception as e:
        return f"Erreur lors de la génération du programme : {str(e)}"


# ═══════════════════════════════════════════════════════════════════════
# 🧪 TEST STANDALONE (avant l'agent)
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("🗺️  Test generate_itinerary — Option 2 (RAG-augmenté)\n")
    print("=" * 70)
    
    resultat = generate_itinerary(
        destination="Venise",
        days=4,
        interests="gastronomie",
        budget="800 euros",
    )
    print(resultat)
    print("=" * 70)