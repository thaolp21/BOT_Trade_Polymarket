"""
Cancel Polymarket CLOB orders placed by order_gpt.py
- Tracks placed orders and cancels them using the Polymarket CLOB API
- Requires py-clob-client and dotenv
"""

import os
import dotenv

from py_clob_client.client import ClobClient

# Load environment variables
dotenv.load_dotenv()

HOST = os.getenv("HOST")
CHAIN_ID = int(os.getenv("CHAIN_ID", "137"))
KEY = os.getenv("KEY")
POLYMARKET_PROXY_ADDRESS = os.getenv("POLYMARKET_PROXY_ADDRESS")
SIGNATURE_TYPE = int(os.getenv("SIGNATURE_TYPE", "1"))


# Directory where order IDs files are stored (written by order_all_markets_repeat.py)
ORDER_IDS_DIR = "order_ids"

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


def load_all_order_ids(order_ids_dir=ORDER_IDS_DIR):
    if not os.path.exists(order_ids_dir):
        print(f"Order IDs directory not found: {order_ids_dir}")
        return []
    order_ids = []
    for fname in os.listdir(order_ids_dir):
        if fname.startswith("placed_order_ids_") and fname.endswith(".txt"):
            fpath = os.path.join(order_ids_dir, fname)
            with open(fpath, "r") as f:
                order_ids.extend([line.strip() for line in f if line.strip()])
    return order_ids

def cancel_orders(client, order_ids):
    if not order_ids:
        print("No order IDs to cancel.")
        return
    # Pass order_ids directly as per Polymarket CLOB client
    try:
        resp = client.cancel_orders(order_ids)
        print("Cancel response:", resp)
    except Exception as e:
        print(f"Error cancelling orders: {e}")

if __name__ == "__main__":
    order_ids = load_all_order_ids()
    print(f"Loaded {len(order_ids)} order IDs to cancel from '{ORDER_IDS_DIR}'.")
    client = prepare_client()
    cancel_orders(client, order_ids)
