"""
Tool get_weather — récupère la météo actuelle d'une ville.
Utilise l'API Open-Meteo (gratuite, sans clé).
Version 2 : avec gestion d'erreurs robuste.
"""

import requests


# Codes météo de Open-Meteo (un extrait des plus communs)
WEATHER_CODES = {
    0: "ciel clair ☀️",
    1: "principalement clair 🌤️",
    2: "partiellement nuageux ⛅",
    3: "couvert ☁️",
    45: "brouillard 🌫️",
    48: "brouillard givrant 🌫️",
    51: "bruine légère 🌦️",
    53: "bruine modérée 🌦️",
    55: "bruine dense 🌧️",
    61: "pluie légère 🌧️",
    63: "pluie modérée 🌧️",
    65: "forte pluie 🌧️",
    71: "neige légère 🌨️",
    73: "neige modérée 🌨️",
    75: "forte neige ❄️",
    80: "averses légères 🌦️",
    81: "averses modérées 🌧️",
    82: "fortes averses ⛈️",
    95: "orage ⛈️",
    96: "orage avec grêle légère ⛈️",
    99: "orage avec grêle forte ⛈️",
}


def get_weather(city: str) -> dict:
    """
    Récupère la météo actuelle d'une ville. Gère les erreurs proprement.
    
    Args:
        city: Nom de la ville (ex: "Paris", "Tokyo")
    
    Returns:
        - Dict avec les infos météo si tout va bien
        - Dict avec {"error": "..."} si problème (ville inconnue, API down, etc.)
    """
    
    try:
        # === ÉTAPE 1 : Géocoder la ville ===
        geo_response = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1, "language": "fr"},
            timeout=5  # Max 5 secondes d'attente
        )
        geo_response.raise_for_status()  # Vérifie le statut HTTP
        geo_data = geo_response.json()
        
        # 🛡️ GESTION D'ERREUR 1 : ville non trouvée
        if not geo_data.get("results"):
            return {"error": f"Ville '{city}' non trouvée. Vérifie l'orthographe."}
        
        location = geo_data["results"][0]
        lat = location["latitude"]
        lon = location["longitude"]
        
        # === ÉTAPE 2 : Récupérer la météo ===
        weather_response = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,weather_code,wind_speed_10m,relative_humidity_2m"
            },
            timeout=5
        )
        weather_response.raise_for_status()
        weather_data = weather_response.json()
        current = weather_data.get("current", {})
        
        return {
            "city": location["name"],
            "country": location.get("country", "?"),
            "temperature": current.get("temperature_2m"),
            "weather": WEATHER_CODES.get(current.get("weather_code"), "conditions inconnues"),
            "wind_speed": current.get("wind_speed_10m"),
            "humidity": current.get("relative_humidity_2m")
        }
    
    # 🛡️ GESTION D'ERREUR 2 : timeout (API met trop de temps)
    except requests.Timeout:
        return {"error": "L'API météo met trop de temps à répondre. Réessaie."}
    
    # 🛡️ GESTION D'ERREUR 3 : pas de réseau / API down
    except requests.ConnectionError:
        return {"error": "Impossible de joindre l'API météo. Vérifie ta connexion."}
    
    # 🛡️ GESTION D'ERREUR 4 : toute autre erreur imprévue
    except Exception as e:
        return {"error": f"Erreur inattendue : {str(e)}"}


# === TEST ===
if __name__ == "__main__":
    print("🌍 Test de get_weather (avec gestion d'erreurs)\n")
    
    villes = ["Paris", "Atlantide", "Tokyo", "Xyz123Bidon", "New York"]
    
    for ville in villes:
        print(f"━━━ {ville} ━━━")
        result = get_weather(ville)
        
        # 🛡️ Gérer le cas d'erreur
        if "error" in result:
            print(f"   ❌ {result['error']}")
        else:
            print(f"   📍 Ville      : {result['city']}, {result['country']}")
            print(f"   🌡️  Température : {result['temperature']}°C")
            print(f"   🌥️  Conditions  : {result['weather']}")
            print(f"   💨 Vent        : {result['wind_speed']} km/h")
            print(f"   💧 Humidité    : {result['humidity']}%")
        print()
    
    print("✅ Test terminé sans crash, même avec des villes bidons !")