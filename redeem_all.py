"""
Automated Polymarket CTF Redemption Script (all-in-one)
- Prompts for missing .env values (Polygon RPC, WALLET_ADDRESS, PRIVATE_KEY)
- Fetches all conditionIds from Polymarket API
- Fetches all redeemable positions for your wallet
- Redeems all positions in one run
- Installs web3 and python-dotenv if missing
"""

import os
import sys
import json
import subprocess
import time
from getpass import getpass

# --- Dependency check and install ---
REQUIRED = ["web3", "python-dotenv", "requests"]
for pkg in REQUIRED:
    try:
        __import__(pkg if pkg != "python-dotenv" else "dotenv")
    except ImportError:
        print(f"Installing missing package: {pkg}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])


import requests
from web3 import Web3
from dotenv import load_dotenv
from py_clob_client.client import ClobClient

# --- Prompt for .env values if missing ---
def ensure_env(var, prompt, secret=False, default=None):
    val = os.getenv(var)
    if not val:
        if secret:
            val = getpass(f"Enter {prompt}: ")
        else:
            val = input(f"Enter {prompt}{' ['+default+']' if default else ''}: ") or default
        with open(".env", "a") as f:
            f.write(f"{var}={val}\n")
        os.environ[var] = val
    return val


load_dotenv()
POLYGON_RPC = ensure_env("POLYGON_RPC", "Polygon RPC URL", default="https://polygon-rpc.com")
WALLET_ADDRESS = Web3.to_checksum_address(ensure_env("WALLET_ADDRESS", "0xBFA11f805Ff3D330afef83EFEAA7d6285F4e2A21"))
PRIVATE_KEY = ensure_env("KEY", "your private key", secret=True)

CTF_ADDRESS = Web3.to_checksum_address(ensure_env("CTF_ADDRESS", "CTF contract address", default="0x4D97DCd97eC945f40cF65F87097ACe5EA0476045"))
COLLATERAL_TOKEN = Web3.to_checksum_address(ensure_env("USDC_ADDRESS", "collateral token address", default="0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"))  # USDC on Polygon

# --- Get all conditionIds from saved market_condition_ids folder ---
def get_condition_ids_from_folder(specific_file=None):
    import json
    import time as _time
    folder = "market_condition_ids"
    ids = set()
    now = int(_time.time())
    if specific_file:
        # Only check the specific file
        fpath = specific_file
        if os.path.isfile(fpath):
            with open(fpath, "r") as f:
                try:
                    data = json.load(f)
                    cid = data.get("condition_id")
                    ts = data.get("timestamp", 0)
                    # Only include if at least 4 hours old
                    if cid and now - ts >= 4 * 60 * 60:
                        ids.add(cid)
                except Exception:
                    pass
        return list(ids)
    # Otherwise, check all files
    if not os.path.exists(folder):
        print(f"Condition ID folder '{folder}' does not exist.")
        return []
    for fname in os.listdir(folder):
        fpath = os.path.join(folder, fname)
        if os.path.isfile(fpath):
            with open(fpath, "r") as f:
                try:
                    data = json.load(f)
                    cid = data.get("condition_id")
                    ts = data.get("timestamp", 0)
                    if cid and now - ts >= 4 * 60 * 60:
                        ids.add(cid)
                except Exception:
                    continue
    return list(ids)

# --- CTF ABI (minimal) ---
CTF_ABI = [
    {
        "constant": True,
        "inputs": [
            {"name": "account", "type": "address"},
            {"name": "id", "type": "uint256"}
        ],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [
            {"name": "conditionId", "type": "bytes32"}
        ],
        "name": "getOutcomeSlotCount",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [
            {"name": "collateralToken", "type": "address"},
            {"name": "parentCollectionId", "type": "bytes32"},
            {"name": "conditionId", "type": "bytes32"},
            {"name": "indexSets", "type": "uint[]"}
        ],
        "name": "redeemPositions",
        "outputs": [],
        "type": "function"
    }
]

def get_position_id(collateral, condition_id, outcome_index):
    return Web3.solidity_keccak(
        ["address", "bytes32", "uint256[]"],
        [collateral, condition_id, [outcome_index]]
    )

def fetch_redeemable_positions(ctf, condition_ids):
    redeemable = []
    checked_condition_ids = set()
    for condition_id in condition_ids:
        try:
            slot_count = ctf.functions.getOutcomeSlotCount(condition_id).call()
        except Exception as e:
            continue
        found = False
        for outcome_index in range(slot_count):
            position_id = get_position_id(COLLATERAL_TOKEN, condition_id, outcome_index)
            print(f"[DEBUG] position_id: {position_id.hex() if isinstance(position_id, bytes) else position_id}")
            # Convert position_id to integer for ABI compatibility
            if isinstance(position_id, bytes):
                position_id_int = int.from_bytes(position_id, "big")
            elif isinstance(position_id, str):
                position_id_int = int(position_id, 16)
            else:
                position_id_int = position_id
            try:
                balance = ctf.functions.balanceOf(WALLET_ADDRESS, position_id_int).call()
                print(f"  Balance: {balance}")
            except Exception as e:
                print(f"[DEBUG] Exception in balanceOf for {position_id_int}: {e}")
                continue
            if balance > 0:
                redeemable.append({
                    "collateral": COLLATERAL_TOKEN,
                    "conditionId": condition_id,
                    "outcomeIndex": outcome_index,
                    "balance": balance
                })
                found = True
        if found:
            checked_condition_ids.add(condition_id)
    return redeemable, checked_condition_ids

def redeem_positions(w3, ctf, positions):
    from collections import defaultdict
    acct = w3.eth.account.from_key(PRIVATE_KEY)
    grouped = defaultdict(list)
    for pos in positions:
        key = (pos["collateral"], pos["conditionId"])
        grouped[key].append(pos["outcomeIndex"])
    for (collateral, condition_id), outcome_indexes in grouped.items():
        index_set = sum([1 << i for i in outcome_indexes])
        print(f"Redeeming: collateral={collateral}, conditionId={condition_id}, indexSet={index_set}")
        tx = ctf.functions.redeemPositions(
            collateral,
            b"\x00" * 32,
            condition_id,
            [index_set]
        ).build_transaction({
            'from': acct.address,
            'nonce': w3.eth.get_transaction_count(acct.address),
            'gas': 300000,
            'gasPrice': w3.eth.gas_price,
        })
        signed = acct.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
        print(f"Sent redeem tx: {tx_hash.hex()}")
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"Redeem receipt: {receipt}")

def main():
    w3 = Web3(Web3.HTTPProvider(POLYGON_RPC))
    ctf = w3.eth.contract(address=CTF_ADDRESS, abi=CTF_ABI)
    print(f"Connected to Polygon: {w3.is_connected()}")
    print('ctf address:', ctf.address)
    print('wallet address:', WALLET_ADDRESS)
    import sys
    specific_file = sys.argv[1] if len(sys.argv) > 1 else None
    if specific_file:
        print(f"Checking only file: {specific_file}")
    print("Fetching all conditionIds from saved market_condition_ids folder...")
    # condition_ids = get_condition_ids_from_folder(specific_file)
    condition_ids = ['0xeae9ec2ca3f0f75ddf37d0242e99f1fa2528efd1d0cb945e5b746f478ae368e3']
    print(f"Found {len(condition_ids)} conditionIds from folder.")
    print(condition_ids)
    # To use the API fetch instead, comment above and uncomment below:
    # condition_ids = fetch_condition_ids()
    # print(f"Found {len(condition_ids)} conditionIds from API.")
    print("Scanning for redeemable positions...")
    positions, checked_condition_ids = fetch_redeemable_positions(ctf, condition_ids)
    print(f"Found {len(positions)} redeemable positions.")
    if not positions:
        print("No redeemable positions found.")
        return
    print("Redeeming positions...")
    redeem_positions(w3, ctf, positions)
    # After redeeming, delete checked conditionId files
    folder = "market_condition_ids"
    for cid in checked_condition_ids:
        for fname in os.listdir(folder):
            fpath = os.path.join(folder, fname)
            if os.path.isfile(fpath):
                with open(fpath, "r") as f:
                    file_cid = f.read().strip()
                if file_cid == cid:
                    try:
                        os.remove(fpath)
                        print(f"Deleted checked file: {fpath}")
                    except Exception as e:
                        print(f"Error deleting file {fpath}: {e}")
    print("Redeem All done.")

if __name__ == "__main__":
    main()
