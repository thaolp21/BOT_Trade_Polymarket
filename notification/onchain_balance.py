import os
import sys
import json
import requests
from dotenv import load_dotenv

load_dotenv()

POLYGON_RPC = os.getenv("POLYGON_RPC", "https://polygon-rpc.com")
TARGET_ADDRESS = "0xBFA11f805Ff3D330afef83EFEAA7d6285F4e2A21"
USDC_ADDRESS = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"  # canonical USDC on Polygon
USDC_DECIMALS = 6


def normalize_address(addr: str) -> str:
    if not addr.startswith("0x"):
        raise ValueError("Address must start with 0x")
    if len(addr) != 42:
        raise ValueError("Address must be 42 chars including 0x")
    return addr.lower()


def build_balance_of_call(wallet_address: str) -> str:
    # function signature balanceOf(address) -> 0x70a08231
    sig = "70a08231"
    wallet_clean = normalize_address(wallet_address)[2:]
    # pad wallet address to 32 bytes (64 hex chars)
    data = "0x" + sig + ("0" * 24) + wallet_clean  # 24 zeros = 12 bytes to make 32 bytes total after 20-byte address
    # NOTE: 32 bytes needs 64 hex chars. We added 24 leading zeros + 40 address hex chars = 64.
    return data


def eth_call(rpc_url: str, to: str, data: str, timeout: int = 15) -> str:
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "eth_call",
        "params": [
            {
                "to": to,
                "data": data
            },
            "latest"
        ]
    }
    r = requests.post(rpc_url, json=payload, timeout=timeout)
    r.raise_for_status()
    out = r.json()
    if 'error' in out:
        raise RuntimeError(out['error'])
    return out.get('result')


def get_erc20_balance(rpc_url: str, token_address: str, wallet_address: str, decimals: int) -> dict:
    token_address = normalize_address(token_address)
    wallet_address = normalize_address(wallet_address)
    data = build_balance_of_call(wallet_address)
    raw_hex = eth_call(rpc_url, token_address, data)
    if not raw_hex or not raw_hex.startswith("0x"):
        raise RuntimeError("Invalid eth_call result")
    raw_int = int(raw_hex, 16)
    human = raw_int / (10 ** decimals)
    return {
        'token': token_address,
        'wallet': wallet_address,
        'raw': raw_int,
        'decimals': decimals,
        'human': human
    }


def main():
    rpc = POLYGON_RPC
    if not rpc:
        print("Missing POLYGON_RPC in environment.")
        sys.exit(1)

    wallet = os.environ.get('QUERY_WALLET') or TARGET_ADDRESS
    token = os.environ.get('QUERY_TOKEN') or USDC_ADDRESS
    try:
        bal = get_erc20_balance(rpc, token, wallet, USDC_DECIMALS)
        print(json.dumps(bal, indent=2))
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
