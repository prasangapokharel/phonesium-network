#!/usr/bin/env python3
"""Transfer 100M PHN from genesis owner to user's owner address"""

import requests
import hashlib
import orjson
import time
import random
import ecdsa
from datetime import datetime

NODE_URL = "http://localhost:8765"

# Genesis owner (current holder of 100M PHN)
GENESIS_OWNER = {
    "private_key": "eb87a303da00dabb8e0c599030f1387f89d0984e561fa2af4a7d6b7bdcbffb07",
    "public_key": "f4e24f24529bd72dfd35dddbf4d4f0cfefebdfd819aa3571fb12923748b95e9f8ab18cac571432bb012c68b35e30b4ce91fec4463043f2d813c867a150d08366",
    "address": "PHNb722d6062a8fde00cd300bf40315289f061fcb6d"
}

# User's owner address (will receive 100M PHN)
USER_OWNER = {
    "address": "PHN0a2e1f46a128caa0fded990ac8f7c9fb5e7da8a6"
}

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def make_txid(sender, recipient, amount, fee, timestamp, nonce):
    s = f"{sender}{recipient}{amount}{fee}{timestamp}{nonce}"
    return hashlib.sha256(s.encode()).hexdigest()

def sign_transaction(tx_data, private_key):
    tx_copy = dict(tx_data)
    tx_copy.pop("signature", None)
    tx_json = orjson.dumps(tx_copy, option=orjson.OPT_SORT_KEYS)
    sk = ecdsa.SigningKey.from_string(bytes.fromhex(private_key), curve=ecdsa.SECP256k1)
    signature = sk.sign(tx_json)
    return signature.hex()

def main():
    log("=" * 70)
    log("TRANSFERRING 100,000,000 PHN FROM GENESIS OWNER TO USER OWNER")
    log("=" * 70)
    
    # Check genesis owner balance first
    log("\nChecking genesis owner balance...")
    try:
        resp = requests.post(
            f"{NODE_URL}/get_balance",
            json={"address": GENESIS_OWNER["address"]},
            timeout=5
        )
        genesis_balance = resp.json().get("balance", 0)
        log(f"Genesis Owner Balance: {genesis_balance:,.2f} PHN")
        
        if genesis_balance < 100000000:
            log("ERROR: Genesis owner doesn't have 100M PHN!")
            return False
    except Exception as e:
        log(f"ERROR checking balance: {e}")
        return False
    
    # Create transaction
    amount = 100000000.0  # 100 million PHN
    fee = 0.02
    timestamp = time.time()
    nonce = random.randint(0, 999999)
    
    txid = make_txid(
        GENESIS_OWNER["public_key"],
        USER_OWNER["address"],
        amount, fee, timestamp, nonce
    )
    
    tx_data = {
        "txid": txid,
        "sender": GENESIS_OWNER["public_key"],  # MUST be public key!
        "recipient": USER_OWNER["address"],
        "amount": amount,
        "fee": fee,
        "timestamp": timestamp,
        "nonce": nonce,
        "sender_public_key": GENESIS_OWNER["public_key"]
    }
    
    # Sign with genesis owner's private key
    log("\nSigning transaction...")
    signature = sign_transaction(tx_data, GENESIS_OWNER["private_key"])
    tx_data["signature"] = signature
    
    log("\nTransaction Details:")
    log(f"  From: {GENESIS_OWNER['address']}")
    log(f"  To:   {USER_OWNER['address']}")
    log(f"  Amount: {amount:,.2f} PHN")
    log(f"  Fee: {fee} PHN")
    log(f"  TXID: {txid}")
    
    # Send transaction
    log("\nSending transaction to node...")
    try:
        response = requests.post(
            f"{NODE_URL}/send_tx",
            json={"tx": tx_data},
            timeout=10
        )
        
        if response.status_code == 200:
            log("\n[SUCCESS] Transaction sent!")
            result = response.json()
            log(f"Response: {result}")
            log("\nTransaction is now in mempool.")
            log("Miners are already running - waiting for block to mine...")
            return True
        else:
            log(f"\n[ERROR] Transaction failed: {response.status_code}")
            log(f"Response: {response.text}")
            return False
    except Exception as e:
        log(f"\n[ERROR] Failed to send transaction: {e}")
        return False

if __name__ == "__main__":
    try:
        success = main()
        if success:
            log("\n" + "="*70)
            log("Transfer transaction submitted successfully!")
            log("Waiting for miners to process it...")
            log("="*70)
    except Exception as e:
        log(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
