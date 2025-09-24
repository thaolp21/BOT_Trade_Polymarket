"""
Script to place orders for all markets in a list of slugs (from Polymarket API).
Keeps the original order.py script for EXAMPLE_MARKET_SLUG testing.
"""

import requests
import json
import os
import logging
from typing import List
from order import prepare_client, build_orders, post_batch_orders
from order_specs_generator import generate_specs
from find_market_by_slug import find_market_by_slug

# --- Logging setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[logging.StreamHandler()]
)

# API endpoint for list of markets
MARKET_LIST_API = "https://gamma-api.polymarket.com/events/pagination?limit=100&active=true&archived=false&tag_slug=15M&closed=false&order=volume24hr&ascending=false&offset=0"

# Get list of market slugs from API

def get_market_slugs() -> List[str]:
    resp = requests.get(MARKET_LIST_API, timeout=20)
    resp.raise_for_status()
    data = resp.json().get("data", [])
    slugs = []
    for market in data:
        slug = market.get("slug")
        if slug:
            if "btc-up-or-down" not in slug:
                continue
            slugs.append(slug)
    return slugs

if __name__ == "__main__":
    slugs = get_market_slugs()
    logging.info(f"Found {len(slugs)} market slugs.")
    client = prepare_client()
    for slug in slugs:
        try:
            market = find_market_by_slug(slug)
            token_ids = json.loads(market["clobTokenIds"])
            start_time_str = market["eventStartTime"]
            logging.info(f"Placing orders for market: {slug} | eventStartTime: {start_time_str}")
            all_specs = generate_specs(start_time_str)
            batches = [
                all_specs[i : i + 15]  # 15 is MAX_ORDERS_PER_BATCH
                for i in range(0, len(all_specs), 15)
            ]
            for idx, specs_batch in enumerate(batches, 1):
                orders = build_orders(client, token_ids, specs_batch)
                logging.info(f"Posting batch {idx} for {slug} with {len(orders)} orders...")
                resp = post_batch_orders(client, orders, order_ids_file=f"placed_order_ids_{slug}.txt")
                logging.info(f"Response: {resp}")
                
        except Exception as e:
            logging.error(f"Failed to place orders for market {slug}: {e}")
