import os
import json
from web3 import Web3
from dotenv import load_dotenv

# --- Load environment variables ---
load_dotenv()
RPC_URL = os.getenv("POLYGON_RPC")
PK = os.getenv("KEY")
PROXY_WALLET_FACTORY_ADDRESS = os.getenv("PROXY_WALLET_FACTORY_ADDRESS")
CONDITIONAL_TOKENS_FRAMEWORK_ADDRESS = os.getenv("CONDITIONAL_TOKENS_FRAMEWORK_ADDRESS")
USDC_ADDRESS = os.getenv("USDC_ADDRESS")

# --- Load ABIs ---
with open(os.path.join(os.path.dirname(__file__), "proxyFactoryAbi.json")) as f:
    proxy_factory_abi = json.load(f)
with open(os.path.join(os.path.dirname(__file__), "conditionalTokensAbi.json")) as f:
    ctf_abi = json.load(f)

# --- Connect to Polygon ---
w3 = Web3(Web3.HTTPProvider(RPC_URL))
from web3.middleware import geth_poa_middleware
w3.middleware_onion.inject(geth_poa_middleware, layer=0)
w3 = Web3(Web3.HTTPProvider(RPC_URL))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)
acct = w3.eth.account.from_key(PK)
wallet = acct.address
print(f"Using wallet: {wallet}")

# --- Prepare redeem call data ---
def encode_redeem(collateral, condition_id):
    # This encodes the redeemPositions function call
    ctf_contract = w3.eth.contract(address=CONDITIONAL_TOKENS_FRAMEWORK_ADDRESS, abi=ctf_abi)
    tx = ctf_contract.functions.redeemPositions(
        collateral, b"\x00"*32, condition_id, [1, 2]
    ).build_transaction({'from': wallet})
    return tx['data']
condition_ids = ['0xeae9ec2ca3f0f75ddf37d0242e99f1fa2528efd1d0cb945e5b746f478ae368e3']
data = encode_redeem(USDC_ADDRESS, condition_ids[0])

# --- Prepare proxy transaction ---
factory = w3.eth.contract(address=PROXY_WALLET_FACTORY_ADDRESS, abi=proxy_factory_abi)
proxy_txn = {
    "to": Web3.to_checksum_address(CONDITIONAL_TOKENS_FRAMEWORK_ADDRESS),
    "typeCode": 1,
    "data": data,
    "value": 0
}

# --- Build and send transaction ---
txn = factory.functions.proxy([proxy_txn], {"gasPrice": w3.toWei("100", "gwei")}).build_transaction({
    "from": wallet,
    "nonce": w3.eth.get_transaction_count(wallet),
    "gas": 500000
})
signed = acct.sign_transaction(txn)
tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
print("Txn hash:", tx_hash.hex())
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
print("Redeem complete. Receipt:", receipt)
