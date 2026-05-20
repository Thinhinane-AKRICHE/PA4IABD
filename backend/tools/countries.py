import requests
from typing import Dict, Any, List, Optional


_COUNTRIES_CACHE: Dict[str, Dict[str, Any]] = {}


def get_country_info(country_name: str) -> Dict[str, Any]:
    cache_key = country_name.lower().strip()
    if cache_key in _COUNTRIES_CACHE:
        return _COUNTRIES_CACHE[cache_key]
    
    try:
        response = requests.get(
            f"https://restcountries.com/v3.1/name/{country_name}",
            params={"fullText": "false"},
            timeout=5
        )
        response.raise_for_status()
        data = response.json()
        
        if not data or len(data) == 0:
            return {"error": f"Pays '{country_name}' non trouvé."}
        
        country = data[0]
        
        name_fr = country.get("translations", {}).get("fra", {}).get("common", "")
        if not name_fr:
            name_fr = country.get("name", {}).get("common", country_name)
        
        capital = country.get("capital", [])
        capital = capital[0] if capital else "Non renseignée"
        
        continents = country.get("continents", [])
        continent = continents[0] if continents else "Non renseigné"
        
        languages_dict = country.get("languages", {})
        languages = list(languages_dict.values())
        
        currencies_dict = country.get("currencies", {})
        currencies = []
        for code, info in currencies_dict.items():
            name = info.get("name", code)
            symbol = info.get("symbol", "")
            currencies.append(f"{name} ({code}){' ' + symbol if symbol else ''}")
        currency = currencies[0] if currencies else "Non renseignée"
        
        timezones = country.get("timezones", [])
        timezone = ", ".join(timezones[:3]) if timezones else "Non renseigné"
        
        population = country.get("population", 0)
        flag = country.get("flag", "")
        country_code = country.get("cca3", "")
        region = country.get("region", "")
        subregion = country.get("subregion", "")
        
        result = {
            "name_fr": name_fr,
            "name_en": country.get("name", {}).get("common", ""),
            "capital": capital,
            "continent": continent,
            "region": region,
            "subregion": subregion,
            "languages": languages,
            "currency": currency,
            "timezone": timezone,
            "population": population,
            "flag": flag,
            "country_code": country_code,
            "area_km2": country.get("area", 0),
            "borders": country.get("borders", []),
            "maps_google": country.get("maps", {}).get("googleMaps", ""),
        }
        
        _COUNTRIES_CACHE[cache_key] = result
        return result
    
    except requests.Timeout:
        return {"error": "L'API RestCountries met trop de temps à répondre."}
    except requests.ConnectionError:
        return {"error": "Impossible de joindre l'API RestCountries."}
    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return {"error": f"Pays '{country_name}' non trouvé."}
        return {"error": f"Erreur HTTP {e.response.status_code}"}
    except Exception as e:
        return {"error": f"Erreur inattendue : {str(e)}"}


def search_country_by_city(city: str) -> Optional[str]:
    try:
        response = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1, "language": "fr"},
            timeout=5
        )
        response.raise_for_status()
        data = response.json()
        
        if not data.get("results"):
            return None
        
        location = data["results"][0]
        country_code = location.get("country_code", "")
        country_name = location.get("country", "")
        
        if country_code:
            country_info = get_country_info(country_name)
            if "error" not in country_info:
                return country_info.get("name_fr", country_name)
        
        return country_name
    except Exception:
        return None


def get_all_countries() -> List[Dict[str, str]]:
    try:
        response = requests.get(
            "https://restcountries.com/v3.1/all",
            params={"fields": "name,translations,flag,cca3"},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        countries = []
        for country in data:
            name_fr = country.get("translations", {}).get("fra", {}).get("common", "")
            if not name_fr:
                name_fr = country.get("name", {}).get("common", "")
            
            countries.append({
                "name_fr": name_fr,
                "name_en": country.get("name", {}).get("common", ""),
                "flag": country.get("flag", ""),
                "code": country.get("cca3", "")
            })
        
        countries.sort(key=lambda x: x["name_fr"])
        return countries
    except Exception as e:
        return [{"error": f"Impossible de récupérer la liste des pays : {str(e)}"}]