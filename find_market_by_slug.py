import requests
from typing import Dict
import os
from dotenv import load_dotenv

load_dotenv()

GAMMA_API = os.getenv("GAMMA_API", "https://gamma-api.polymarket.com")

def find_market_by_slug(slug: str) -> Dict:
    """Query Gamma API to find market object by slug. Returns market dict or raises."""
    url = f"{GAMMA_API}/markets"
    params = {"slug": slug}
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()
    # Gamma GET /markets may return list or object depending on the API - handle both:
    if isinstance(data, dict) and "markets" in data:
        markets = data["markets"]
    elif isinstance(data, list):
        markets = data
    elif isinstance(data, dict) and data:
        # sometimes returns single market object
        markets = [data]
    else:
        markets = []

    # Try to find exact slug match
    for m in markets:
        if m.get("slug") == slug or m.get("market_slug") == slug:
            return m

    # fallback: return first with market_slug containing slug
    if markets:
        return markets[0]

    raise ValueError(
        f"Market with slug '{slug}' not found via Gamma API. Response length: {len(markets)}"
    )