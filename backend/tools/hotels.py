import os
import requests
from dotenv import load_dotenv
from tools.rag import search_rag

load_dotenv()

GEOAPIFY_API_KEY = os.environ["GEOAPIFY_API_KEY"]


def geocode_city(city: str):
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


def search_hotels(lat: float, lon: float, limit: int = 10):
    url = "https://api.geoapify.com/v2/places"
    params = {
        "categories": "accommodation.hotel",
        "filter": f"circle:{lon},{lat},5000",  # rayon 5 km
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
            hotels.append({"nom": nom, "adresse": adresse})

        return hotels

    except Exception as e:
        print(f"Erreur recherche hôtels : {type(e).__name__}: {e}")
        return []


def get_hotels_geoapify(city: str) -> str:
    coords = geocode_city(city)
    if coords is None:
        return f"Impossible de localiser '{city}'."

    lat, lon = coords
    hotels = search_hotels(lat, lon)

    if not hotels:
        return f"Aucun hôtel trouvé pour '{city}' via Geoapify."

    lignes = [f"Hôtels à {city} :"]
    for h in hotels:
        if h["nom"] != "Hôtel sans nom":
            lignes.append(f"  • {h['nom']} — {h['adresse']}")

    return "\n".join(lignes)


def get_hotels(city: str) -> str:
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
        rag_result = search_rag(city, "hôtels se loger hébergement budget")
        rag_advice = str(rag_result)[:800]
    except Exception as e:
        print(f"RAG indisponible : {e}")
        rag_advice = ""

    if geoapify_ok:
        response = geoapify_result
        if rag_advice:
            response += f"\n\nConseils d'hébergement (Wikivoyage) :\n{rag_advice}"
        response += (
            "\n\nPour les prix exacts et réserver, "
            "consultez Booking.com, Expedia ou un site local."
        )
        return response
    elif rag_advice:
        return (
            f"Conseils d'hébergement pour {city} (Wikivoyage) :\n"
            f"{rag_advice}\n\n"
            "Pour des hôtels précis et réserver, consultez Booking.com."
        )
    else:
        return (
            f"Désolé, je n'ai pas d'information d'hébergement pour "
            f"{city} actuellement. Je te conseille de consulter "
            "Booking.com ou un office de tourisme local."
        )