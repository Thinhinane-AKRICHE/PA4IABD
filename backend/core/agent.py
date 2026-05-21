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
    Recherche des informations touristiques sur une destination dans Wikivoyage.
    Utiliser pour toute question sur une ville : musées, restaurants, attractions, histoire, culture.
    
    Args:
        destination: Nom de la ville
        query: Sujet recherché
    
    Returns:
        Informations touristiques
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
    Récupère la météo actuelle d'une ville.
    
    Args:
        city: Nom de la ville
    
    Returns:
        Informations météo actuelles
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
def get_country_info(country_name: str) -> str:
    """
    Récupère les informations officielles sur un pays.
    
    Args:
        country_name: Nom du pays
    
    Returns:
        Informations détaillées sur le pays
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
    Recherche des hôtels et hébergements dans une ville.
    
    Args:
        city: Nom de la ville
    
    Returns:
        Liste d'hôtels et conseils d'hébergement
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
    Génère un itinéraire de voyage structuré jour par jour.
    
    Args:
        destination: Ville de destination
        days: Nombre de jours
        interests: Centres d'intérêt
        budget: Budget du voyage
    
    Returns:
        Itinéraire détaillé
    """
    return generate_itinerary(destination, days, interests, budget)


SYSTEM_PROMPT = """Tu es Travel Buddy, un assistant voyage francophone expert et personnalisé.

OUTILS DISPONABLES

- search_destination_info : infos touristiques sur une VILLE
- get_weather_info : météo actuelle
- get_hotels_info : hôtels et hébergements
- create_travel_plan : générer un itinéraire structuré
- get_country_info : infos sur un PAYS

IMPORTANT

Tu n'as JAMAIS les prix des hôtels, oriente vers Booking/Expedia.

STYLE

- Français chaleureux et professionnel
- Personnalise naturellement selon le profil utilisateur
- Si info manquante, dis-le honnêtement
"""


class TravelBuddyAgent:
    
    def __init__(self):
        
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
            get_country_info,
            get_hotels_info,
            create_travel_plan
        ]
        
        print("Agent Travel Buddy prêt\n")
    
    
    def chat(
        self, 
        message: str, 
        user_id: int, 
        thread_id: str = None
    ) -> Dict[str, Any]:
        
        profile = get_user_profile(user_id)
        
        if "error" not in profile:
            profile_json = format_profile_for_agent(profile)
            profile_section = f"""

PROFIL UTILISATEUR:
{profile_json}

Utilise ces informations systématiquement pour :
1. Filtrer les hôtels selon le budget
2. Respecter le régime alimentaire et allergies (CRITIQUE)
3. Suggérer des hôtels adaptés (étoiles, équipements)
4. Privilégier les activités selon les centres d'intérêt
5. Favoriser les destinations favorites, éviter la blacklist
6. Vérifier l'accessibilité si contraintes de mobilité
"""
        else:
            profile_section = "\n\nAucun profil utilisateur disponible.\n"
        
        full_system_prompt = SYSTEM_PROMPT + profile_section
        
        agent_executor = create_react_agent(
            self.llm,
            self.tools,
            checkpointer=self.memory,
        )
        
        if thread_id is None:
            import uuid
            thread_id = f"user-{user_id}-{uuid.uuid4().hex[:8]}"
        
        config = {"configurable": {"thread_id": thread_id}}
        
        system_message = SystemMessage(content=full_system_prompt)
        
        inputs = {
            "messages": [
                system_message,
                ("user", message)
            ]
        }
        
        response_text = ""
        tools_used = []
        
        try:
            for chunk in agent_executor.stream(inputs, config, stream_mode="values"):
                message_obj = chunk["messages"][-1]
                
                if hasattr(message_obj, 'content') and message_obj.content:
                    response_text = message_obj.content
                
                if hasattr(message_obj, 'tool_calls') and message_obj.tool_calls:
                    for tool_call in message_obj.tool_calls:
                        tools_used.append(tool_call.get('name', 'unknown'))
            
            print(f"Réponse générée (tools utilisés: {tools_used})")
            
            return {
                "response": response_text or "Désolé, je n'ai pas pu générer de réponse.",
                "thread_id": thread_id,
                "tools_used": list(set(tools_used)),
                "user_id": user_id
            }
        
        except Exception as e:
            print(f"Erreur agent : {e}")
            raise RuntimeError(f"Erreur lors de l'exécution de l'agent: {str(e)}")
    
    
    def close(self):
        print("\nFermeture du pool de connexions Neon")
        self.pool.close()


import atexit

def cleanup():
    print("\nFermeture du pool de connexions Neon...")

atexit.register(cleanup)