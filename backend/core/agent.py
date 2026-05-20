import os
from typing import Dict, Any
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.postgres import PostgresSaver
from psycopg_pool import ConnectionPool
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage

from tools.rag import search_rag
from tools.weather import get_weather
from tools.profile import get_user_profile, format_profile_for_agent
from tools.countries import get_country_info as fetch_country_info
from tools.hotels import get_hotels           
from tools.itinerary import generate_itinerary 

load_dotenv()


@tool
def search_destination_info(destination: str, query: str) -> str:
    """
    OBLIGATOIRE pour TOUTE question touristique sur une ville.
    
    Tu DOIS appeler cette fonction pour CHAQUE question concernant 
    une destination, MÊME si tu penses connaître la réponse.
    
    Cette fonction interroge Wikivoyage en français, qui contient des 
    informations OFFICIELLES, À JOUR et SOURCÉES.
    
    Ne JAMAIS répondre à une question sur une ville sans appeler ce tool.
    
    Args:
        destination: Nom de la ville (ex: 'Paris', 'Tokyo', 'Bordeaux')
        query: Sujet recherché (ex: 'visiter', 'musées', 'restaurants')
    
    Returns:
        str: Informations touristiques de Wikivoyage
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
    
    Returns:
        str: Informations météo actuelles
    """
    result = get_weather(city)
    
    if "error" in result:
        return f"Erreur : {result['error']}"
    
    return (
        f"A {result['city']} ({result['country']}) actuellement : "
        f"{result['temperature']}°C, {result['weather']}. "
        f"Vent : {result['wind_speed']} km/h. "
        f"Humidite : {result['humidity']}%."
    )


@tool
def get_profile_info(user_id: int = 1) -> str:
    """
    Récupère le profil et préférences enregistrées d'un utilisateur
    (budget, type de voyage, préférences hôtels, contraintes
    alimentaires, destinations favorites, langue).
    
    Utilise ce tool si l'utilisateur demande "mon profil",
    "mes préférences", ou pour adapter une réponse à son profil.
    
    Args:
        user_id: identifiant de l'utilisateur (ex: 1)
    
    Returns:
        str: Profil utilisateur formaté
    """
    profile = get_user_profile(user_id)
    
    if "error" in profile:
        return f"Erreur : {profile['error']}"
    
    return format_profile_for_agent(profile)


@tool
def get_country_info(country_name: str) -> str:
    """
    Récupère les informations officielles sur un pays (capitale, langue, 
    monnaie, fuseau horaire, population, superficie).
    
    À utiliser quand l'utilisateur demande des infos sur un PAYS 
    (pas une ville) : capitale, langue, monnaie, drapeau, population, etc.
    
    Args:
        country_name: Nom du pays (ex: 'France', 'Japon', 'Brésil')
    
    Returns:
        str: Informations détaillées sur le pays
    """
    result = fetch_country_info(country_name)
    
    if "error" in result:
        return f"Erreur : {result['error']}"
    
    borders_text = ""
    if result.get("borders"):
        borders_text = f"\nFrontières : {', '.join(result['borders'])}"
    
    return (
        f"{result['name_fr']} ({result['name_en']}) :\n"
        f"Capitale : {result['capital']}\n"
        f"Continent : {result['continent']} ({result['region']}, {result['subregion']})\n"
        f"Langues : {', '.join(result['languages'])}\n"
        f"Monnaie : {result['currency']}\n"
        f"Fuseau horaire : {result['timezone']}\n"
        f"Population : {result['population']:,} habitants\n"
        f"Superficie : {result['area_km2']:,} km²\n"
        f"Code ISO : {result['country_code']}"
        f"{borders_text}"
    )


@tool
def get_hotels_info(city: str) -> str:
    """
    OBLIGATOIRE pour TOUTE question sur les hôtels / hébergement / où dormir.
    
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
    
    Returns:
        str: Liste d'hôtels et conseils d'hébergement
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
    OBLIGATOIRE pour TOUTE demande de PROGRAMME / ITINÉRAIRE / PLAN de voyage.
    
    Tu DOIS appeler cette fonction dès que l'utilisateur demande un 
    "programme", un "itinéraire", un "plan de X jours", "que faire en 
    X jours", etc. — MÊME si tu penses pouvoir le faire toi-même.
    
    Génère un programme structuré jour par jour, ancré dans Wikivoyage.
    
    Args:
        destination: Ville (ex: 'Lyon', 'Paris')
        days: Nombre de jours (ex: 5)
        interests: Centres d'intérêt mentionnés (ex: 'musées, gastronomie')
        budget: Budget mentionné (ex: '1000 euros')
    
    Returns:
        str: Itinéraire détaillé jour par jour
    """
    return generate_itinerary(destination, days, interests, budget)


SYSTEM_PROMPT = """Tu es Travel Buddy, un assistant voyage francophone amical et expert.

Tu DOIS utiliser tes outils pour répondre — ne te base JAMAIS sur ta connaissance générale.

WORKFLOW OBLIGATOIRE :
1. Au début de CHAQUE nouvelle conversation, appelle get_profile_info(user_id=1)
2. Adapte TOUTES tes suggestions selon ce profil :
   - HOTELS : Filtre par budget, étoiles, équipements ESSENTIELS (BLOQUANTS)
   - RESTAURANTS : Respecte le régime alimentaire et les allergies
   - ACTIVITES : Adapte selon les centres d'intérêt
   - DESTINATIONS : Privilégie les favorites, ne suggère JAMAIS les destinations en blacklist

OUTILS DISPONIBLES :
- search_destination_info : pour TOUTE question touristique sur une VILLE
  (musées, restaurants, attractions, culture, transports, histoire, gastronomie, etc.)
- get_weather_info : pour TOUTE question sur la météo
- get_hotels_info : pour TOUTE question sur les hôtels ou l'hébergement
- create_travel_plan : pour générer un PROGRAMME / ITINÉRAIRE de voyage structuré
- get_profile_info(user_id=1) : pour charger le profil utilisateur
- get_country_info : pour des infos sur un PAYS (capitale, langue, monnaie, etc.)

RÈGLES STRICTES :
1. Appelle TOUJOURS get_profile_info(user_id=1) au début de chaque conversation
2. Si l'utilisateur demande des infos sur une VILLE, tu DOIS appeler 
   search_destination_info, MÊME si tu penses connaître la réponse
3. Si l'utilisateur demande des infos sur un PAYS (capitale, langue, monnaie, 
   population), tu DOIS appeler get_country_info
4. Si l'utilisateur demande la MÉTÉO, tu DOIS appeler get_weather_info
5. Si l'utilisateur demande des HÔTELS ou de l'HÉBERGEMENT, tu DOIS appeler 
   get_hotels_info, MÊME si :
   - un budget est mentionné (ex: "j'ai 500€")
   - tu as DÉJÀ donné des hôtels plus tôt dans la conversation
   - tu penses connaître des hôtels de cette ville
6. Si l'utilisateur demande un PROGRAMME, un ITINÉRAIRE ou un PLAN de 
   voyage (X jours), tu DOIS appeler create_travel_plan
7. Tu ne réponds JAMAIS à partir de tes connaissances internes seules
8. Tes réponses se basent EXCLUSIVEMENT sur ce que tes tools retournent
9. Tu n'INVENTES JAMAIS de noms d'hôtels. Tu utilises UNIQUEMENT ceux que 
   get_hotels_info retourne
10. Ne suggère JAMAIS un hôtel sans les équipements essentiels du profil
11. Respecte TOUJOURS le régime alimentaire pour les restaurants

RÈGLE PRIX / BUDGET (TRÈS IMPORTANT) :
Tu n'as JAMAIS accès aux prix exacts des hôtels (aucun de tes outils ne 
les fournit). Si l'utilisateur donne un budget :
- Appelle QUAND MÊME get_hotels_info pour avoir les vrais hôtels
- Donne les conseils de budget issus de Wikivoyage (quartiers, gammes)
- Dis HONNÊTEMENT que tu n'as pas les prix en temps réel, et oriente 
  vers Booking.com / Expedia pour vérifier le budget et réserver
- Ne prétends JAMAIS qu'un hôtel "rentre dans le budget" : tu ne 
  connais pas son prix

AUTRES RÈGLES :
- Réponds toujours en français, chaleureux et structuré
- Si tu ne trouves pas l'info dans les tools, dis-le honnêtement
"""


class TravelBuddyAgent:
    """
    Agent de voyage IA avec mémoire persistante.
    """
    
    def __init__(self):
        """Initialise l'agent et la connexion à Neon Postgres."""
        
        database_url = os.environ["DATABASE_URL"]
        
        connection_kwargs = {
            "autocommit": True,
            "prepare_threshold": 0,
        }
        
        self.pool = ConnectionPool(
            conninfo=database_url,
            max_size=20,
            kwargs=connection_kwargs,
        )
        
        self.memory = PostgresSaver(self.pool)
        self.memory.setup()
        
        print("Connexion à Neon Postgres établie")
        
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        
        self.tools = [
            search_destination_info, 
            get_weather_info, 
            get_profile_info,
            get_country_info,
            get_hotels_info,
            create_travel_plan
        ]
        
        self.system_message = SystemMessage(content=SYSTEM_PROMPT)
        
        self.agent_executor = create_react_agent(
            self.llm,
            self.tools,
            checkpointer=self.memory,
        )
        
        print("Agent Travel Buddy pret\n")
    
    
    def chat(
        self, 
        message: str, 
        user_id: int = 1, 
        thread_id: str = None
    ) -> Dict[str, Any]:
        """
        Envoie un message à l'agent et récupère la réponse.
        
        Args:
            message: Le message de l'utilisateur
            user_id: ID de l'utilisateur
            thread_id: ID de la conversation (généré si non fourni)
        
        Returns:
            Dict contenant la réponse, le thread_id et les outils utilisés
        """
        
        if thread_id is None:
            import uuid
            thread_id = f"user-{user_id}-{uuid.uuid4().hex[:8]}"
        
        config = {"configurable": {"thread_id": thread_id}}
        
        inputs = {
            "messages": [
                self.system_message,
                ("user", message)
            ]
        }
        
        response_text = ""
        tools_used = []
        
        try:
            for chunk in self.agent_executor.stream(inputs, config, stream_mode="values"):
                message_obj = chunk["messages"][-1]
                
                if hasattr(message_obj, 'content') and message_obj.content:
                    response_text = message_obj.content
                
                if hasattr(message_obj, 'tool_calls') and message_obj.tool_calls:
                    for tool_call in message_obj.tool_calls:
                        tools_used.append(tool_call.get('name', 'unknown'))
            
            return {
                "response": response_text or "Désolé, je n'ai pas pu générer de réponse.",
                "thread_id": thread_id,
                "tools_used": list(set(tools_used))
            }
        
        except Exception as e:
            raise RuntimeError(f"Erreur lors de l'exécution de l'agent: {str(e)}")
    
    
    def clear_conversation(self, thread_id: str):
        """
        Supprime l'historique d'une conversation.
        
        Args:
            thread_id: ID de la conversation à supprimer
        """
        print(f"Suppression de conversation non implémentée pour {thread_id}")
        pass
    
    
    def close(self):
        """Ferme proprement le pool de connexions."""
        print("\nFermeture du pool de connexions Neon")
        self.pool.close()


import atexit

def cleanup():
    print("\nFermeture du pool de connexions Neon...")

atexit.register(cleanup)