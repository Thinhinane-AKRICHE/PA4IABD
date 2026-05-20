"""
═══════════════════════════════════════════════════════════════════════
  agent.py — Agent IA Travel Buddy V5
  
  Architecture moderne avec mémoire PERSISTANTE sur Neon Postgres
  ─────────────────────────────────────────────────────────────────────
  - LangChain : ChatOpenAI + @tool decorator
  - LangGraph : create_react_agent + PostgresSaver
  - Neon      : PostgreSQL serverless (mémoire + profils utilisateurs)
  
  Tools : search_destination_info (RAG Wikivoyage)
          + get_weather_info     (API Open-Meteo)
          + get_hotels_info      (Geoapify + RAG hybride)
          + create_travel_plan   (itinéraire RAG-augmenté)
          + get_user_profile     (profil utilisateur Postgres)  
═══════════════════════════════════════════════════════════════════════
"""

import os
from dotenv import load_dotenv

# === IMPORTS LANGCHAIN / LANGGRAPH ===
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.postgres import PostgresSaver  # Mémoire persistante
from psycopg_pool import ConnectionPool                   # Pool de connexions
from langchain_core.tools import tool

# === IMPORTS DE NOS PROPRES TOOLS ===
from rag import search_rag                  # Tool 1 : recherche Wikivoyage
from weather import get_weather             # Tool 2 : météo Open-Meteo
from hotels import get_hotels               # Tool 3 : hôtels Geoapify + RAG
from itinerary import generate_itinerary    # Tool 4 : itinéraire RAG-augmenté
from user_profile import load_user_profile  # Tool 5 : profil utilisateur 

# Charge les variables d'environnement depuis .env
load_dotenv()


# ═══════════════════════════════════════════════════════════════════════
# 🔧 SECTION 1 : Wrapper nos fonctions en TOOLS LangChain
# ═══════════════════════════════════════════════════════════════════════


@tool
def search_destination_info(destination: str, query: str) -> str:
    """
    ⚠️ OBLIGATOIRE pour TOUTE question touristique sur une ville.
    
    Tu DOIS appeler cette fonction pour CHAQUE question concernant 
    une destination, MÊME si tu penses connaître la réponse.
    
    Cette fonction interroge Wikivoyage en français, qui contient des 
    informations OFFICIELLES, À JOUR et SOURCÉES.
    
    Ne JAMAIS répondre à une question sur une ville sans appeler ce tool.
    
    Args:
        destination: Nom de la ville (ex: 'Paris', 'Tokyo', 'Bordeaux')
        query: Sujet recherché (ex: 'visiter', 'musées', 'restaurants')
    """
    try:
        results = search_rag(destination, query)
        
        if isinstance(results, dict):
            if "documents" in results and results["documents"]:
                chunks = results["documents"][0][:5]
                return "\n\n---\n\n".join(chunks)
            if "error" in results:
                return f"Erreur : {results['error']}"
        
        if isinstance(results, list):
            return "\n\n---\n\n".join(results[:5])
        
        return str(results)
    
    except Exception as e:
        return f"Erreur lors de la recherche : {str(e)}"


@tool
def get_weather_info(city: str) -> str:
    """
    Récupère la météo actuelle d'une ville (température, conditions, vent, humidité).
    À utiliser dès que l'utilisateur demande le temps, la météo, 
    s'il pleut, la température, etc.
    
    Args:
        city: Nom de la ville (ex: 'Paris', 'Tokyo')
    """
    result = get_weather(city)
    
    if "error" in result:
        return f"❌ {result['error']}"
    
    return (
        f"À {result['city']} ({result['country']}) actuellement : "
        f"{result['temperature']}°C, {result['weather']}. "
        f"Vent : {result['wind_speed']} km/h. "
        f"Humidité : {result['humidity']}%."
    )


@tool
def get_hotels_info(city: str) -> str:
    """
    ⚠️ OBLIGATOIRE pour TOUTE question sur les hôtels / hébergement / où dormir.
    
    Tu DOIS appeler cette fonction pour CHAQUE question concernant 
    le logement dans une ville, MÊME si :
    - un budget est mentionné (ex: "mon budget est 500€")
    - tu as déjà donné des hôtels plus tôt dans la conversation
    - tu penses connaître la réponse
    
    Cette fonction retourne de VRAIS hôtels (Geoapify) + des conseils 
    Wikivoyage. Elle ne fournit PAS les prix exacts : ne prétends 
    JAMAIS connaître le prix d'un hôtel.
    
    Args:
        city: Nom de la ville (ex: 'Paris', 'Lyon', 'Alger')
    """
    return get_hotels(city)


@tool
def create_travel_plan(
    destination: str,
    days: int = 3,
    interests: str = "",
    budget: str = "",
) -> str:
    """
    ⚠️ OBLIGATOIRE pour TOUTE demande de PROGRAMME / ITINÉRAIRE / PLAN de voyage.
    
    Tu DOIS appeler cette fonction dès que l'utilisateur demande un 
    "programme", un "itinéraire", un "plan de X jours", "que faire en 
    X jours", etc. — MÊME si tu penses pouvoir le faire toi-même.
    
    Génère un programme structuré jour par jour, ancré dans Wikivoyage.
    
    Args:
        destination: Ville (ex: 'Lyon', 'Paris')
        days: Nombre de jours (ex: 5)
        interests: Centres d'intérêt mentionnés (ex: 'musées, gastronomie')
        budget: Budget mentionné (ex: '1000 euros')
    """
    return generate_itinerary(destination, days, interests, budget)


@tool
def get_user_profile(user_id: str = "user_001") -> str:
    """
    Récupère le profil et préférences enregistrées d'un utilisateur
    (budget, type de voyage, préférences hôtels, contraintes
    alimentaires, destinations favorites, langue).
    
    Utilise ce tool si l'utilisateur demande "mon profil",
    "mes préférences", ou pour adapter une réponse à son profil.
    
    Args:
        user_id: identifiant de l'utilisateur (ex: 'user_001')
    """
    profil = load_user_profile(user_id)
    if not profil:
        return f"Aucun profil trouvé pour '{user_id}'."
    
    return (
        f"Profil de {profil['nom']} :\n"
        f"- Langue : {profil['langue']}\n"
        f"- Budget voyage : {profil['budget']}\n"
        f"- Type de voyage : {profil['type_voyage']}\n"
        f"- Préférences hôtels : {profil['prefs_hotels']}\n"
        f"- Contraintes alimentaires : {profil['contraintes_alim']}\n"
        f"- Destinations favorites : {profil['destinations_fav']}"
    )


# ═══════════════════════════════════════════════════════════════════════
# 🧠 SECTION 2 : Configuration de la MÉMOIRE PERSISTANTE (Neon)
# ═══════════════════════════════════════════════════════════════════════


# Récupère l'URL de la base Neon depuis .env
DATABASE_URL = os.environ["NEON_DATABASE_URL"]

# Configuration du pool de connexions PostgreSQL
connection_kwargs = {
    "autocommit": True,
    "prepare_threshold": 0,
}

# Pool de connexions vers Neon
pool = ConnectionPool(
    conninfo=DATABASE_URL,
    max_size=20,
    kwargs=connection_kwargs,
)

# Le checkpointer PostgreSQL : stocke la mémoire dans Neon
memory = PostgresSaver(pool)

# Création des tables (idempotent = sûr d'appeler à chaque démarrage)
memory.setup()

print("✅ Connexion à Neon Postgres établie + tables vérifiées\n")


# ═══════════════════════════════════════════════════════════════════════
# 🤖 SECTION 3 : Configuration de l'agent
# ═══════════════════════════════════════════════════════════════════════


# System prompt STRICT — force le tool calling (Tool Calling Reliability)
SYSTEM_PROMPT = """Tu es Travel Buddy, un assistant voyage francophone amical et expert.

Tu DOIS utiliser tes outils pour répondre — ne te base JAMAIS sur ta connaissance générale.

OUTILS DISPONIBLES :
- search_destination_info : pour TOUTE question touristique sur une ville
  (musées, restaurants, attractions, culture, transports, histoire, gastronomie, etc.)
- get_weather_info : pour TOUTE question sur la météo
- get_hotels_info : pour TOUTE question sur les hôtels ou l'hébergement
- create_travel_plan : pour générer un PROGRAMME / ITINÉRAIRE de voyage structuré
- get_user_profile : pour consulter le profil/préférences enregistrées

RÈGLES STRICTES :
1. Si l'utilisateur demande des infos sur une VILLE, tu DOIS appeler 
   search_destination_info, MÊME si tu penses connaître la réponse.
2. Si l'utilisateur demande la MÉTÉO, tu DOIS appeler get_weather_info.
3. Si l'utilisateur demande des HÔTELS ou de l'HÉBERGEMENT, tu DOIS appeler 
   get_hotels_info, MÊME si :
   - un budget est mentionné (ex: "j'ai 500€")
   - tu as DÉJÀ donné des hôtels plus tôt dans la conversation
   - tu penses connaître des hôtels de cette ville
4. Si l'utilisateur demande un PROGRAMME, un ITINÉRAIRE ou un PLAN de 
   voyage (X jours), tu DOIS appeler create_travel_plan.
5. Tu ne réponds JAMAIS à partir de tes connaissances internes seules.
6. Tu n'INVENTES JAMAIS de noms d'hôtels. Tu utilises UNIQUEMENT ceux que 
   get_hotels_info retourne.
7. Si un PROFIL UTILISATEUR est fourni dans le message, tu DOIS adapter 
   TOUTES tes réponses à ces préférences (budget, type de voyage, 
   contraintes alimentaires, etc.) sans que l'utilisateur ait à les répéter.

RÈGLE PRIX / BUDGET (TRÈS IMPORTANT) :
Tu n'as JAMAIS accès aux prix exacts des hôtels (aucun de tes outils ne 
les fournit). Si l'utilisateur donne un budget :
- Appelle QUAND MÊME get_hotels_info pour avoir les vrais hôtels.
- Donne les conseils de budget issus de Wikivoyage (quartiers, gammes).
- Dis HONNÊTEMENT que tu n'as pas les prix en temps réel, et oriente 
  vers Booking.com / Expedia pour vérifier le budget et réserver.
- Ne prétends JAMAIS qu'un hôtel "rentre dans le budget" : tu ne 
  connais pas son prix.

AUTRES RÈGLES :
- Réponds toujours en français, chaleureux et structuré.
- Si tu ne trouves pas l'info dans les tools, dis-le honnêtement.
"""

# Le LLM : GPT-4.1 Nano avec température 0 (déterministe pour choix de tools)
# llm = ChatOpenAI(model="gpt-4.1-nano", temperature=0)

from backend.llm_factory import get_llm

llm = get_llm(
    provider="openai",
    model="gpt-4.1-nano",
    temperature=0
)

# Liste des tools disponibles pour l'agent
tools = [
    search_destination_info,
    get_weather_info,
    get_hotels_info,
    create_travel_plan,
    get_user_profile,
]

# 🎯 CRÉATION DE L'AGENT
agent_executor = create_react_agent(
    llm,                       # Le LLM
    tools,                     # Les tools disponibles
    checkpointer=memory,       # Mémoire PERSISTANTE sur Neon !
    prompt=SYSTEM_PROMPT,      # La personnalité
)


# ═══════════════════════════════════════════════════════════════════════
# 💬 SECTION 4 : Fonction de chat avec streaming + personnalisation
# ═══════════════════════════════════════════════════════════════════════


def chat_with_agent(question: str, thread_id: str = "thread-1", user_id: str = None):
    """
    Pose une question à l'agent.
    Si user_id est fourni → on injecte son profil pour personnaliser.
    
    Args:
        question: La question de l'utilisateur
        thread_id: ID de la conversation (historique dans Neon)
        user_id: ID de l'utilisateur (pour charger son profil)
    """
    
    config = {"configurable": {"thread_id": thread_id}}
    
    # 🆕 INJECTION du profil : personnalisation FIABLE (pas via tool)
    if user_id:
        profil = load_user_profile(user_id)
        if profil:
            question = (
                f"[PROFIL UTILISATEUR — adapte ta réponse à ces préférences :\n"
                f"Nom : {profil['nom']} | Langue : {profil['langue']} | "
                f"Budget : {profil['budget']} | Type : {profil['type_voyage']} | "
                f"Hôtels : {profil['prefs_hotels']} | "
                f"Alimentaire : {profil['contraintes_alim']} | "
                f"Destinations favorites : {profil['destinations_fav']}]\n\n"
                f"Question : {question}"
            )
    
    inputs = {"messages": [("user", question)]}
    
    print(f"\n💬 Toi : {question}")
    print("=" * 70)
    
    for chunk in agent_executor.stream(inputs, config, stream_mode="values"):
        message = chunk["messages"][-1]
        if isinstance(message, tuple):
            print(message)
        else:
            message.pretty_print()
    
    print("=" * 70 + "\n")


# ═══════════════════════════════════════════════════════════════════════
# 🧪 SECTION 5 : Tests
# ═══════════════════════════════════════════════════════════════════════


if __name__ == "__main__":
    print("🌍 Agent Travel Buddy V5 — démarrage\n")
    
    # On ne dit RIEN sur le budget/régime → l'agent doit le savoir SEUL
    chat_with_agent(
        "Propose-moi un programme de 3 jours à Lyon",
        thread_id="thread-perso-test",
        user_id="user_001"
    )
    
    # Autres tests (à décommenter) :
    # chat_with_agent("Quelles sont mes préférences ?", thread_id="thread-perso-test", user_id="user_001")
    # chat_with_agent("Et la météo là-bas ?", thread_id="thread-perso-test", user_id="user_001")  # mémoire


# ═══════════════════════════════════════════════════════════════════════
# 🧹 Cleanup : ferme le pool de connexions proprement
# ═══════════════════════════════════════════════════════════════════════
import atexit

def cleanup():
    """Ferme le pool de connexions Neon quand Python s'arrête."""
    print("\n🧹 Fermeture du pool de connexions Neon...")
    pool.close()

atexit.register(cleanup)