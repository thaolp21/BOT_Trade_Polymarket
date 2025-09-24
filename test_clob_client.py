"""
Script to test basic functions of py_clob_client.ClobClient for Polymarket CLOB.
- Connects to the CLOB
- Gets API credentials
- Gets account info
- Gets open orders (if any)
- Prints results for manual inspection
"""

import os
import dotenv
from py_clob_client.client import ClobClient
import json
from py_clob_client.clob_types import TradeParams

with open("data.json", "r") as f:
    data = json.load(f)
    print('lenghth', len(data))
# Load environment variables
dotenv.load_dotenv()

HOST = os.getenv("HOST", "https://clob.polymarket.com")
KEY = os.getenv("KEY", "")
CHAIN_ID = int(os.getenv("CHAIN_ID", "137"))
POLYMARKET_PROXY_ADDRESS = os.getenv("POLYMARKET_PROXY_ADDRESS", "")
SIGNATURE_TYPE = int(os.getenv("SIGNATURE_TYPE", "2"))

if __name__ == "__main__":
    print("--- Testing ClobClient ---")
    client = ClobClient(
        HOST,
        key=KEY,
        chain_id=CHAIN_ID,
        signature_type=SIGNATURE_TYPE,
        funder=POLYMARKET_PROXY_ADDRESS,
    )
    print("Client initialized.")

    # Test: derive API credentials
    api_creds = client.create_or_derive_api_creds()
    print("API Credentials:", api_creds)

    # Test: set API credentials
    client.set_api_creds(api_creds)
    print("API credentials set.")

    # 1. Fetch your orders
    # orders = client.get_trades(params=TradeParams(
    #     maker_address=POLYMARKET_PROXY_ADDRESS,
    #     market='0x0c5537e4931c39e0fabdff747f9a702d263bb5e595f094c315fe50192f3b6b76'))
    # print(orders)
    # client.cancel_all()
    orders = client.get_orders()
    print(f"Fetched {len(orders)} open orders:")
    # print("api_keys", client.get_api_keys())

    # Test: get trades (matched orders/trade history)
    # condition_ids = set()
    # try:
    #     trades = client.get_trades(TradeParams(
    #     maker_address=client.get_address()
    # ),)
    #     for trade in trades:
    #         cid = trade.get("market")
    #         if cid:
    #             condition_ids.add(cid)
    # except Exception as e:
    #     print("Error getting trades:", e)
    # print(f"Fetched {len(trades)} trades", condition_ids)
    # try:
    #     account_info = client.get_account_info()
    #     print("Account info:", account_info)
    # except Exception as e:
    #     print("Error getting account info:", e)

    print("--- ClobClient test complete ---")
