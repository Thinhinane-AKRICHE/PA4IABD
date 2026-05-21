import os
import requests
from dotenv import load_dotenv
from tools.rag import search_rag

load_dotenv()

GEOAPIFY_API_KEY = os.environ["GEOAPIFY_API_KEY"]


def geocode_city(city: str):
    """Géolocalise une ville via Geoapify."""
    url = "https://api.geoapify.com/v1/geocode/search"
    params = {
        "text": city,
        "type": "city",
        "limit": 1,
        "apiKey": GEOAPIFY_API_KEY,
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        features = data.get("features", [])
        if not features:
            print(f"Ville '{city}' introuvable (geocoding)")
            return None

        props = features[0]["properties"]
        lat = props["lat"]
        lon = props["lon"]
        print(f"{city} → lat={lat}, lon={lon}")
        return (lat, lon)

    except Exception as e:
        print(f"Erreur geocoding : {type(e).__name__}: {e}")
        return None


def search_hotels(lat: float, lon: float, limit: int = 10, radius: int = 15000):
    """Recherche des hôtels autour d'une position."""
    url = "https://api.geoapify.com/v2/places"
    params = {
        "categories": "accommodation.hotel",
        "filter": f"circle:{lon},{lat},{radius}",
        "limit": limit,
        "apiKey": GEOAPIFY_API_KEY,
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        hotels = []
        for feature in data.get("features", []):
            props = feature["properties"]
            nom = props.get("name", "Hôtel sans nom")
            adresse = props.get("formatted", "Adresse non disponible")
            
            # Ignorer les résultats sans nom
            if nom == "Hôtel sans nom":
                continue
                
            hotels.append({
                "nom": nom,
                "adresse": adresse,
                "lat": props.get("lat"),
                "lon": props.get("lon")
            })

        print(f"Trouvé {len(hotels)} hôtels dans un rayon de {radius}m")
        return hotels

    except Exception as e:
        print(f"Erreur recherche hôtels : {type(e).__name__}: {e}")
        return []


def get_hotels_geoapify(city: str) -> str:
    """Récupère les hôtels via Geoapify avec fallback progressif."""
    coords = geocode_city(city)
    if coords is None:
        return f"Impossible de localiser '{city}'."

    lat, lon = coords
    
    # Essayer avec un rayon croissant
    for radius in [5000, 10000, 20000]:
        hotels = search_hotels(lat, lon, radius=radius)
        if hotels:
            break
    
    if not hotels:
        return f"Aucun hôtel trouvé pour '{city}' via Geoapify."

    lignes = [f"Hôtels à {city} (via Geoapify) :"]
    for h in hotels[:10]:  
        lignes.append(f"  • {h['nom']}")
        lignes.append(f"    {h['adresse']}")

    return "\n".join(lignes)


def get_hotels(city: str) -> str:
    """
    Récupère des informations sur les hôtels d'une ville.
    Stratégie : Geoapify (API) → Wikivoyage (RAG) → Message générique
    """
    geoapify_result = ""
    try:
        geoapify_result = get_hotels_geoapify(city)
    except Exception as e:
        print(f"Geoapify indisponible : {e}")
        geoapify_result = ""

    geoapify_ok = (
        geoapify_result
        and "Aucun hôtel" not in geoapify_result
        and "Impossible" not in geoapify_result
    )

    rag_advice = ""
    try:
        rag_result = search_rag(city, "hôtels se loger hébergement budget quartiers")
        
        if isinstance(rag_result, dict) and "documents" in rag_result:
            docs = rag_result["documents"][0][:3]  # Top 3 chunks
            rag_advice = "\n\n".join(docs)[:1000]
        elif isinstance(rag_result, list):
            rag_advice = "\n\n".join(rag_result[:3])[:1000]
        else:
            rag_advice = str(rag_result)[:1000]
            
    except Exception as e:
        print(f"RAG indisponible : {e}")
        rag_advice = ""

    if geoapify_ok:
        response = geoapify_result
        if rag_advice:
            response += f"\n\nConseils d'hébergement (Wikivoyage) :\n{rag_advice}"
        response += (
            "\n\nIMPORTANT : Les prix ne sont pas disponibles via cette API. "
            "Pour voir les tarifs exacts et réserver, consultez Booking.com ou Expedia."
        )
        return response
    
    elif rag_advice:
        return (
            f"Conseils d'hébergement pour {city} (Wikivoyage) :\n\n"
            f"{rag_advice}\n\n"
            "Pour des hôtels précis avec prix et réservation, consultez Booking.com ou Expedia."
        )
    
    else:
        return (
            f"Désolé, je n'ai pas pu récupérer d'informations d'hébergement pour {city} actuellement. "
            "Je te conseille de consulter Booking.com, Expedia ou l'office de tourisme local."
        )