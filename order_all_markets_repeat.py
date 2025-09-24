import requests
import json
import os
import logging
from typing import List
from order import prepare_client, build_orders, post_batch_orders
from order_specs_generator import generate_specs
from find_market_by_slug import find_market_by_slug
import time

# --- Persistent order count state ---
ORDER_COUNT_FILE = 'order_count_state.json'
def load_order_count():
    if os.path.exists(ORDER_COUNT_FILE):
        try:
            with open(ORDER_COUNT_FILE, 'r') as f:
                return json.load(f).get('total_orders', 0)
        except Exception:
            return 0
    return 0

def save_order_count(count):
    with open(ORDER_COUNT_FILE, 'w') as f:
        json.dump({'total_orders': count}, f)

total_orders = load_order_count()

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
    while True:
        slugs = get_market_slugs()
        logging.info(f"Found {len(slugs)} market slugs.")
        client = prepare_client()
        market_condition_ids_dir = "market_condition_ids"
        os.makedirs(market_condition_ids_dir, exist_ok=True)
        for slug in slugs:
            try:
                market = find_market_by_slug(slug)
                token_ids = json.loads(market["clobTokenIds"])
                start_time_str = market["eventStartTime"]
                logging.info(f"Placing orders for market: {slug} | eventStartTime: {start_time_str}")
                # Save conditionId for this market
                # import time as _time
                # condition_id = market.get("conditionId") or market.get("condition_id")
                # if condition_id:
                #     now = int(_time.time())
                #     cid_path = os.path.join(market_condition_ids_dir, f"{slug}.txt")
                #     with open(cid_path, "w") as f:
                #         f.write(json.dumps({"condition_id": condition_id, "timestamp": now}))
                #     # Schedule redeem_all.py to run 4 hours later for this specific file
                #     import threading
                #     import subprocess as _subprocess
                #     import sys as _sys
                #     def run_redeem(cid_path=cid_path):
                #         _subprocess.Popen([_sys.executable, "redeem_all.py", cid_path])
                #     t = threading.Timer(4 * 60 * 60, run_redeem)
                #     t.daemon = True
                #     t.start()
                all_specs = generate_specs(start_time_str)
                batches = [
                    all_specs[i : i + 15]  # 15 is MAX_ORDERS_PER_BATCH
                    for i in range(0, len(all_specs), 15)
                ]
                order_ids_dir = "order_ids"
                os.makedirs(order_ids_dir, exist_ok=True)
                for idx, specs_batch in enumerate(batches, 1):
                    orders = build_orders(client, token_ids, specs_batch)
                    logging.info(f"Posting batch {idx} for {slug} with {len(orders)} orders...")
                    # Only save order_ids_file if at least one order in specs_batch is GTC
                    if any(spec.get("order_type") == "GTC" for spec in specs_batch):
                        order_ids_file = os.path.join(order_ids_dir, f"placed_order_ids_{slug}.txt")
                        resp = post_batch_orders(client, orders, order_ids_file=order_ids_file)
                    else:
                        resp = post_batch_orders(client, orders, order_ids_file=None)
                    # Increment and save total_orders after each order is placed
                    total_orders += len(orders)
                    save_order_count(total_orders)
                    # logging.info(f"Response: {resp}")
            except Exception as e:
                logging.error(f"Failed to place orders for market {slug}: {e}")
        logging.info("Sleeping for 3 hours and 1 minutes before next run...")
        time.sleep(3 * 60 * 60 + 60)
