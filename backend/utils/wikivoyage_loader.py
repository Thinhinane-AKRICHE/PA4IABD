"""
Module pour télécharger des articles depuis Wikivoyage.
"""

import requests
from bs4 import BeautifulSoup
import re


def fetch_wikivoyage(city: str, lang: str = "fr") -> str:
    """
    Télécharge l'article Wikivoyage d'une ville et retourne le texte propre.
    
    Args:
        city: Nom de la ville (ex: "Paris", "Tokyo", "New York")
        lang: Code langue ("fr" = français, "en" = anglais)
    
    Returns:
        Le texte de l'article, nettoyé du HTML
    
    Raises:
        ValueError: Si l'article n'existe pas sur Wikivoyage
    """
    
    # 1. Appel à l'API Wikivoyage (MediaWiki action API)
    url = f"https://{lang}.wikivoyage.org/w/api.php"
    params = {
        "action": "parse",
        "page": city,
        "format": "json",
        "prop": "text"
    }
    headers = {
        "User-Agent": "TravelBuddyMaster/1.0 (educational project)"
    }
    
    print(f"📥 Téléchargement de '{city}' depuis Wikivoyage ({lang})...")
    response = requests.get(url, params=params, headers=headers)
    data = response.json()
    
    # 2. Vérifier que l'article existe
    if "error" in data:
        raise ValueError(
            f"❌ Article '{city}' non trouvé sur Wikivoyage ({lang}). "
            f"Vérifie l'orthographe ou essaie une autre langue."
        )
    
    # 3. Extraire le HTML brut
    html = data["parse"]["text"]["*"]
    
    # 4. Nettoyer le HTML avec BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    
    # Supprimer les éléments non pertinents (navigation, infoboxes, références, tableaux, etc.)
    elements_to_remove = ".navbox, .infobox, .reference, .reflist, .geo, table, sup, .mw-editsection, .vcard, .metadata, .toc"
    for tag in soup.select(elements_to_remove):
        tag.decompose()
    
    # 5. Extraire le texte propre
    text = soup.get_text(separator="\n", strip=True)
    
    # 6. Nettoyer les multiples sauts de ligne
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    print(f"✅ {len(text):,} caractères téléchargés pour '{city}'")
    
    return text


# ============================================================
# TEST quand on lance ce fichier directement
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("🧪 TEST de fetch_wikivoyage")
    print("=" * 60 + "\n")
    
    text = fetch_wikivoyage("Paris")
    
    print(f"\n📄 Aperçu (premiers 800 caractères) :\n")
    print(text[:800])
    print("...\n")
    print(f"📊 Longueur totale : {len(text):,} caractères")