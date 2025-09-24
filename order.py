import json
import os
import time
import logging
from typing import List, Dict
import subprocess

# Handle missing dependencies gracefully
try:
    import dotenv
    from py_clob_client.client import ClobClient
    from py_clob_client.clob_types import OrderArgs, OrderType, PostOrdersArgs
    from py_clob_client.order_builder.constants import BUY, SELL
except ImportError as e:
    missing = str(e).split('No module named ')[-1].replace("'", "")
    raise ImportError(f"Required package '{missing}' is not installed. Please install all dependencies with 'pip install python-dotenv py-clob-client'.")

from order_specs_generator import generate_specs


# --- Logging setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[logging.StreamHandler()]
)

dotenv.load_dotenv()

# ---------------- CONFIG - chỉnh tại đây ----------------

HOST = os.getenv("HOST")
CHAIN_ID = int(os.getenv("CHAIN_ID", "137"))
KEY = os.getenv("KEY")
POLYMARKET_PROXY_ADDRESS = os.getenv("POLYMARKET_PROXY_ADDRESS")
SIGNATURE_TYPE = int(os.getenv("SIGNATURE_TYPE", "1"))
MAX_ORDERS_PER_BATCH = 15
EXAMPLE_MARKET_SLUG = os.getenv("EXAMPLE_MARKET_SLUG")
# ---------------------------------------------------------
try:
    from find_market_by_slug import find_market_by_slug  # ensure this file is in the same directory
except ImportError:
    raise ImportError("Module 'get_markets' not found. Please ensure 'get_markets.py' exists in the same directory as 'order_gpt.py'.")


def prepare_client():
    """Prepare and return a ClobClient instance with credentials."""
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
    """Build a list of PostOrdersArgs from specs and token IDs."""
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
            expiration=spec.get("expiration", 0)
        )
        order = client.create_order(order_args)
        post_order = PostOrdersArgs(
            order=order,
            orderType=getattr(OrderType, spec.get("order_type", "GTC")),
        )
        orders.append(post_order)
    return orders


def post_batch_orders(client, orders, order_ids_file="placed_order_ids.txt"):
    """
    Post a batch of orders and save their IDs for cancellation tracking.
    Ensures order IDs are unique in the file.
    """
    try:
        resp = client.post_orders(orders)
    except Exception as e:
        logging.error(f"Error posting orders: {e}")
        return None
    order_ids = set()
    failed_orders = []
    # The response structure may vary; adjust as needed for your API/client
    if isinstance(resp, list):
        for r in resp:
            # Check for success field and log unsuccessful orders
            if isinstance(r, dict):
                if not r.get("success", True):
                    failed_orders.append(r)
                if "orderID" in r:
                    order_ids.add(str(r["orderID"]))
            elif hasattr(r, "orderID"):
                order_ids.add(str(r.orderID))
    elif isinstance(resp, dict) and "orderID" in resp:
        order_ids.add(str(resp["orderID"]))
    elif hasattr(resp, "orderID"):
        order_ids.add(str(resp.orderID))
    if failed_orders:
        for fail in failed_orders:
            logging.warning(f"Order not successful: {fail}")
    if order_ids:
        # Only do file operations if order_ids_file is not None
        if order_ids_file is not None:
            existing = set()
            if os.path.exists(order_ids_file):
                with open(order_ids_file, "r") as f:
                    existing = set(line.strip() for line in f if line.strip())
            new_ids = order_ids - existing
            if new_ids:
                with open(order_ids_file, "a") as f:
                    for oid in new_ids:
                        f.write(oid + "\n")
                logging.info(f"Saved {len(new_ids)} new order IDs to {order_ids_file}.")
            else:
                logging.info("No new order IDs to save.")
        # else:
        #     logging.info("order_ids_file is None, skipping saving order IDs to file.")
    else:
        logging.warning("No order IDs found in response.")
    return resp


if __name__ == "__main__":
    """
    Main execution: place orders and optionally trigger cancellation.
    """
    try:
        market = find_market_by_slug(EXAMPLE_MARKET_SLUG)
    except Exception as e:
        logging.error(f"Failed to find market: {e}")
        exit(1)

    try:
        token_ids = json.loads(market["clobTokenIds"])
        start_time_str = market["eventStartTime"]
    except Exception as e:
        logging.error(f"Error parsing market data: {e}")
        exit(1)
    logging.info(f"eventStartTime - Token IDs: {start_time_str} {token_ids}")

    client = prepare_client()

    all_specs = generate_specs(start_time_str)

    batches = [
        all_specs[i : i + MAX_ORDERS_PER_BATCH]
        for i in range(0, len(all_specs), MAX_ORDERS_PER_BATCH)
    ]

    for idx, specs_batch in enumerate(batches, 1):
        orders = build_orders(client, token_ids, specs_batch)
        logging.info(f"Posting batch {idx} with {len(orders)} orders...")
        # resp = post_batch_orders(client, orders)
        # logging.info(f"Response: {resp}")


    #TEST first order in first batch only
    # if batches:
    #     first_batch = batches[0]
    #     if first_batch:
    #         first_order = build_orders(client, token_ids, first_batch)
    #         logging.info(f"Posting first order in first batch with {len(first_order)} orders...")
    #         resp = post_batch_orders(client, first_order)
    #         logging.info(f"Response: {resp}")

    # --- Trigger cancel_orders.py if condition is met (currently always False) ---
    def should_cancel():
        # TODO: Replace with your real condition
        return False  # Set to True to always trigger for testing

    if should_cancel():
        logging.info("Triggering cancel_orders.py...")
        try:
            result = subprocess.run(["python", "cancel_orders.py"], capture_output=True, text=True)
            logging.info(f"cancel_orders.py output:\n{result.stdout}")
            if result.stderr:
                logging.error(f"cancel_orders.py errors:\n{result.stderr}")
        except Exception as e:
            logging.error(f"Failed to run cancel_orders.py: {e}")
