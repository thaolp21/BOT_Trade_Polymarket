# import requests

# API_URL = "https://clob.polymarket.com/markets"

# def get_markets():
#     markets = []
#     cursor = ""
#     while True:
#         url = f"{API_URL}?limit=50&cursor={cursor}"
#         resp = requests.get(url)
#         data = resp.json()
#         markets.extend(data.get("markets", []))
#         cursor = data.get("next_cursor")
#         if not cursor:  # hết trang
#             break
#     return markets

# def filter_btc_markets():
#     all_markets = get_markets()
#     btc_markets = [
#         m for m in all_markets
#         if m.get("market_slug", "").startswith("btc-up-or-down-15m")
#     ]
#     return btc_markets

# if __name__ == "__main__":
#     btc = filter_btc_markets()
#     for m in btc:
#         print("Slug:", m["market_slug"])
#         print("Title:", m.get("question"))
#         print("ID:", m["id"])
#         print("End date:", m.get("end_date_iso"))
#         print("-" * 50)

import requests
import json

def get_current_events():
    url = "https://strapi-matic.poly.market/markets"
    params = {
        "active": "true",
        "_sort": "end_date:asc",
        "type": "binary",
        "slug_contains": "btc-up-or-down-15m"
    }
    
    response = requests.get(url, params=params)
    if response.status_code == 200:
        events = response.json()
        for event in events:
            print(f"Slug: {event['slug']}, End Date: {event['end_date']}")
        return events
    else:
        print(f"Error: {response.status_code}")
        return None

# Lấy thông tin sự kiện
events = get_current_events()