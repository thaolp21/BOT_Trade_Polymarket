"""
Listen to Polymarket user-channel for order match events using official websocket-client template.
Tracks orders placed by order_gpt.py (order IDs in placed_order_ids.txt).
Prints a message when any of your orders is matched (filled/partially filled).

Docs: https://docs.polymarket.com/quickstart/websocket/WSS-Quickstart
"""

from py_clob_client.client import ClobClient
import os
import json
import time
import threading
from websocket import WebSocketApp
import dotenv

dotenv.load_dotenv()

HOST = os.getenv("HOST", "https://clob.polymarket.com")
KEY = os.getenv("KEY", "")
CHAIN_ID = int(os.getenv("CHAIN_ID", "137"))
POLYMARKET_PROXY_ADDRESS = os.getenv("POLYMARKET_PROXY_ADDRESS", "")
SIGNATURE_TYPE = int(os.getenv("SIGNATURE_TYPE", "1"))
ORDER_IDS_FILE = "placed_order_ids.txt"

# Initialize client and get API credentials
client = ClobClient(HOST, key=KEY, chain_id=CHAIN_ID, signature_type=SIGNATURE_TYPE, funder=POLYMARKET_PROXY_ADDRESS)

api_creds = client.create_or_derive_api_creds()
api_key = api_creds.api_key
api_secret = api_creds.api_secret
api_passphrase = api_creds.api_passphrase

def load_tracked_order_ids():
    if not os.path.exists(ORDER_IDS_FILE):
        return set()
    with open(ORDER_IDS_FILE, "r") as f:
        return {line.strip() for line in f if line.strip()}

USER_CHANNEL = "user"

class UserWebSocket:
    def __init__(self, url, auth, tracked_orders):
        self.url = url
        self.auth = auth
        self.tracked_orders = tracked_orders
        self.ws = WebSocketApp(
            url + "/ws/" + USER_CHANNEL,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open,
        )

    def on_message(self, ws, message):
        try:
            if not message or not message.strip() or message == "PONG":
                #PING and PONG are special messages used to keep the websocket connection alive.
                #Your script sends a "PING" every 10 seconds (see the ping method).
                #The server replies with "PONG" to acknowledge and keep the connection open.
                return  # Ignore empty and PONG messages
            data = json.loads(message)
            # Look for order update events
            if data.get("type") == "order_update":
                order_id = str(data.get("orderId"))
                status = data.get("status")
                filled = data.get("filledSize")
                if order_id in self.tracked_orders:
                    print(f"Order matched! ID: {order_id}, Status: {status}, Filled: {filled}")
        except Exception as e:
            print(f"Error parsing message: {e} | Raw: {message}")

    def on_error(self, ws, error):
        print("Error: ", error)
        exit(1)

    def on_close(self, ws, close_status_code, close_msg):
        print("closing")
        exit(0)

    def on_open(self, ws):
        # Subscribe to user channel with auth
        ws.send(json.dumps({"markets": [], "type": USER_CHANNEL, "auth": self.auth}))
        thr = threading.Thread(target=self.ping, args=(ws,))
        thr.start()

    def ping(self, ws):
        try:
            while True:
                if not ws.keep_running:
                    break
                try:
                    ws.send("PING")
                except Exception as e:
                    # Exit thread quietly if connection is closed
                    break
                time.sleep(10)
        except KeyboardInterrupt:
            pass

    def run(self):
        self.ws.run_forever()

if __name__ == "__main__":
    url = "wss://ws-subscriptions-clob.polymarket.com"
    auth = {"apiKey": api_key, "secret": api_secret, "passphrase": api_passphrase}
    tracked_orders = load_tracked_order_ids()
    print(f"Tracking {len(tracked_orders)} order IDs.")
    user_ws = UserWebSocket(url, auth, tracked_orders)
    user_ws.run()
