import os
import sys
import json
import time
from datetime import datetime, timezone
from typing import Optional, Tuple

# Add project root to path for utils import
CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from utils.common import r2

import requests
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

load_dotenv()

POLYMARKET_ADDRESS = os.getenv("POLYMARKET_PROXY_ADDRESS") or "0xBFA11f805Ff3D330afef83EFEAA7d6285F4e2A21"
PNL_API = "https://user-pnl-api.polymarket.com/user-pnl"
VALUE_API = "https://data-api.polymarket.com/value"

SESSION = requests.Session()
DEFAULT_TIMEOUT = 15

# On-chain (Polygon) USDC details
POLYGON_RPC = os.getenv("POLYGON_RPC", "https://polygon-rpc.com")
USDC_ADDRESS = (os.getenv("USDC_ADDRESS") or "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174").lower()
USDC_DECIMALS = 6


def fetch_json(url: str, params: dict) -> Optional[object]:
    try:
        r = SESSION.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None


def get_latest_pnl(address: str) -> Optional[float]:
    params = {
        'user_address': address,
        'interval': 'all',
        'fidelity': '1d'
    }
    data = fetch_json(PNL_API, params)
    if not isinstance(data, list) or not data:
        return None
    # Assume list sorted ascending by time; take last
    latest = data[-1]
    p = latest.get('p')
    return float(p) if isinstance(p, (int, float)) else 0


def get_pending_claimable(address: str) -> Optional[float]:
    params = {
        'user': address
    }
    data = fetch_json(VALUE_API, params)
    if not isinstance(data, list) or not data:
        return None
    item = data[0]
    val = item.get('value')
    return float(val) if isinstance(val, (int, float)) else None


def to_iso(ts: Optional[int]) -> str:
    if ts is None:
        return ''
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


# ---------------- On-chain balance helpers ---------------- #
def _normalize_address(addr: str) -> str:
    if not addr.startswith('0x') or len(addr) != 42:
        raise ValueError('Invalid address format')
    return addr.lower()


def _build_balance_of_call(wallet_address: str) -> str:
    sig = '70a08231'  # balanceOf(address)
    wallet_clean = _normalize_address(wallet_address)[2:]
    return '0x' + sig + ('0' * 24) + wallet_clean


def _eth_call_balance(token_address: str, wallet_address: str) -> Optional[int]:
    try:
        payload = {
            'jsonrpc': '2.0',
            'id': 1,
            'method': 'eth_call',
            'params': [
                {
                    'to': token_address,
                    'data': _build_balance_of_call(wallet_address)
                },
                'latest'
            ]
        }
        r = requests.post(POLYGON_RPC, json=payload, timeout=15)
        r.raise_for_status()
        js = r.json()
        if 'error' in js:
            raise RuntimeError(js['error'])
        raw_hex = js.get('result')
        if not raw_hex or not raw_hex.startswith('0x'):
            return None
        return int(raw_hex, 16)
    except Exception as e:
        print(f"Error eth_call balance: {e}")
        return None


def get_usdc_balance(address: str) -> Optional[float]:
    raw = _eth_call_balance(USDC_ADDRESS, address)
    if raw is None:
        return None
    return raw / (10 ** USDC_DECIMALS)


def main():
    address = POLYMARKET_ADDRESS
    if not address:
        print("Missing POLYMARKET_PROXY_ADDRESS in environment.")
        sys.exit(1)

    summary = generate_summary(address)
    print(json.dumps(summary, indent=2))
    _write_summary(summary)


def generate_summary(address: str = None) -> dict:
    address = address or POLYMARKET_ADDRESS
    latest_pnl = get_latest_pnl(address)
    pending_claimable = get_pending_claimable(address)
    usdc_balance = get_usdc_balance(address)
    total_balance = (usdc_balance or 0) + (pending_claimable or 0)
    gmt7 = ZoneInfo('Asia/Bangkok')
    retrieved_local = datetime.now(gmt7).strftime('%Y-%m-%d %H:%M:%S GMT+7')
    return {
        'retrieved_at': retrieved_local,
        'balance': r2(total_balance, 1),
        'profit': r2(latest_pnl, 1),
        'pending_claimable': r2(pending_claimable, 1),
    }

def _write_summary(summary: dict):
    out_dir = os.path.dirname(__file__)
    combined_path = os.path.join(out_dir, 'combined_notification_data.json')
    try:
        with open(combined_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
        print(f"Saved combined summary -> {combined_path}")
    except Exception as e:
        print(f"Failed saving combined file: {e}")


if __name__ == '__main__':
    main()
