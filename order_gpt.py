import json
import os
import time
import requests
import dotenv
from typing import List, Dict

# py-clob-client imports (from Polymarket doc examples)
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs, OrderType, PostOrdersArgs
from py_clob_client.order_builder.constants import BUY, SELL
from order_specs_generator import generate_specs

dotenv.load_dotenv()

# ---------------- CONFIG - chỉnh tại đây ----------------

HOST = os.getenv("HOST")
CHAIN_ID = int(os.getenv("CHAIN_ID", "137"))
KEY = os.getenv("KEY")
POLYMARKET_PROXY_ADDRESS = os.getenv("POLYMARKET_PROXY_ADDRESS")
SIGNATURE_TYPE = int(os.getenv("SIGNATURE_TYPE", "1"))
MAX_ORDERS_PER_BATCH = 15
GAMMA_API = os.getenv("GAMMA_API", "https://gamma-api.polymarket.com")
EXAMPLE_MARKET_SLUG = os.getenv("EXAMPLE_MARKET_SLUG", "btc-up-or-down-15m")
# ---------------------------------------------------------


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


def prepare_client():
    if SIGNATURE_TYPE == 1:
        client = ClobClient(
            HOST,
            key=KEY,
            chain_id=CHAIN_ID,
            signature_type=1,
            funder=POLYMARKET_PROXY_ADDRESS,
        )
    elif SIGNATURE_TYPE == 2:
        client = ClobClient(
            HOST,
            key=KEY,
            chain_id=CHAIN_ID,
            signature_type=2,
            funder=POLYMARKET_PROXY_ADDRESS,
        )
    else:
        client = ClobClient(HOST, key=KEY, chain_id=CHAIN_ID)
    client.set_api_creds(client.create_or_derive_api_creds())
    return client


def build_orders(client, token_ids, specs):
    """specs is a list of dicts: price, size, side, order_type, outcome_index"""
    orders = []
    for spec in specs[:MAX_ORDERS_PER_BATCH]:
        token_id = token_ids[spec.get("outcome_index", 0)]
        side_const = BUY if spec["side"].lower().startswith("b") else SELL
        order_args = OrderArgs(
            price=float(spec["price"]),
            size=int(spec["size"]),
            side=side_const,
            token_id=token_id,
        )
        order = client.create_order(order_args)
        post_order = PostOrdersArgs(
            order=order,
            orderType=getattr(OrderType, spec.get("order_type", "GTC")),
        )
        orders.append(post_order)
    return orders


def post_batch_orders(client, orders):
    return client.post_orders(orders)


if __name__ == "__main__":
    # load your saved JSON market file
    market = find_market_by_slug(EXAMPLE_MARKET_SLUG)

    # parse token IDs (note JSON stores them as string of JSON list)
    token_ids = json.loads(market["clobTokenIds"])
    print("Token IDs:", token_ids)

    client = prepare_client()

    # 0 - Up, 1 - Down
    # generate 20 specs (10 up + 10 down)
    all_specs = generate_specs()

    # cắt thành nhiều batch <= 15 orders
    batches = [
        all_specs[i : i + MAX_ORDERS_PER_BATCH]
        for i in range(0, len(all_specs), MAX_ORDERS_PER_BATCH)
    ]

    for idx, specs_batch in enumerate(batches, 1):
        orders = build_orders(client, token_ids, specs_batch)
        print(f"Posting batch {idx} with {len(orders)} orders...")
        # resp = post_batch_orders(client, orders)
        # print("Response:", resp)
