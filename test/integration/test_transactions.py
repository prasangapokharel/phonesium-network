#!/usr/bin/env python3
"""
Comprehensive transaction testing script for PHN Blockchain
Tests transaction propagation across all running miners
"""

import requests
import hashlib
import orjson
import time
import random
from datetime import datetime

# Node URL
NODE_URL = "http://localhost:8765"

# Wallet details
WALLETS = {
    "FUND": {
        "address": "PHN0a2e1f46a128caa0fded990ac8f7c9fb5e7da8a6",
        "private_key": "aebfe0c96d56586b9290bd0b2d66f6c486c28fec110cec91e39414eb97bd679f",
        "public_key": "4fdae4ab16c8f4283f262139a71214e80da3a8e6880b5ef52eb0435d95ecdef30801ae7887badcefd54689e32bff9b9f1221bae02dd6556a58a56f07a7b69e12"
    },
    "MINER1": {
        "address": "PHN718b7ad6d46933825778e5c95757e12b853e3d0c",
        "private_key": "6d3bde63c09de2bd2cd1c02ea9e92f71d14d642ac05e5f3895b60f61893cd980",
        "public_key": "22aec866ecd19d1d6e6ebe7c1e832fb7404742c2ba89dff2839d215c17e9ac3d8b9c3f0c6c6f87bc16a3085ebd667e7b3a3307adf62b6308e9bf48524bf8b4bb"
    },
    "MINER2": {
        "address": "PHN2d1395d421654092992c9994aee240e66b91458a",
        "private_key": "055c8e3afd2a9752c66caf3b4de5f36c583ef6a6a001bc2a334ecb2c46eb85d6",
        "public_key": "a9f65cf967a53fdab9a29a1dfec1415b2be7fddb9f56f0b5860c459df43df269a660dc2a9d29316556f9156252568f93ab7b5ab5c177fdb85f96904219766609"
    }
}

def log(message):
    """Print timestamped log message"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def get_balance(address):
    """Get balance for an address"""
    try:
        response = requests.post(
            f"{NODE_URL}/get_balance",
            json={"address": address},
            timeout=5
        )
        if response.status_code == 200:
            return response.json().get("balance", 0)
        return None
    except Exception as e:
        log(f"Error getting balance: {e}")
        return None

def sign_transaction(tx_data, private_key):
    """Sign a transaction using the same logic as base.py"""
    import ecdsa
    
    # Create transaction copy without signature
    tx_copy = dict(tx_data)
    tx_copy.pop("signature", None)
    
    # Serialize with sorted keys
    tx_json = orjson.dumps(tx_copy, option=orjson.OPT_SORT_KEYS)
    
    # Sign with private key
    sk = ecdsa.SigningKey.from_string(bytes.fromhex(private_key), curve=ecdsa.SECP256k1)
    signature = sk.sign(tx_json)
    
    return signature.hex()

def make_txid(sender, recipient, amount, fee, timestamp, nonce):
    """Generate transaction ID"""
    s = f"{sender}{recipient}{amount}{fee}{timestamp}{nonce}"
    return hashlib.sha256(s.encode()).hexdigest()

def send_transaction(sender_name, recipient_name, amount, fee=0.02):
    """Send a transaction from one wallet to another"""
    sender = WALLETS[sender_name]
    recipient = WALLETS[recipient_name]
    
    log(f"Preparing transaction: {sender_name} -> {recipient_name} ({amount} PHN)")
    
    # Generate timestamp and nonce
    timestamp = time.time()
    nonce = random.randint(0, 999999)
    
    # Generate TXID (uses public key as sender, just like blockchain expects)
    txid = make_txid(sender["public_key"], recipient["address"], amount, fee, timestamp, nonce)
    
    # Build transaction (without signature first)
    # IMPORTANT: sender must be PUBLIC KEY for signature verification
    tx_data = {
        "txid": txid,
        "sender": sender["public_key"],  # PUBLIC KEY, not address!
        "recipient": recipient["address"],
        "amount": amount,
        "fee": fee,
        "timestamp": timestamp,
        "nonce": nonce,
        "sender_public_key": sender["public_key"]
    }
    
    # Sign transaction
    signature = sign_transaction(tx_data, sender["private_key"])
    tx_data["signature"] = signature
    
    # Send to node wrapped in "tx" object
    try:
        log(f"Sending transaction to {NODE_URL}/send_tx")
        response = requests.post(
            f"{NODE_URL}/send_tx",
            json={"tx": tx_data},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            log(f"[OK] Transaction sent successfully!")
            if result.get("data"):
                log(f"  TXID: {result['data'].get('txid', 'N/A')}")
                log(f"  Status: {result['data'].get('status', 'N/A')}")
                return result['data'].get('txid')
            return None
        else:
            log(f"[ERROR] Transaction failed: {response.status_code}")
            log(f"  Response: {response.text}")
            return None
    except Exception as e:
        log(f"[ERROR] Error sending transaction: {e}")
        return None

def wait_for_mining(seconds=10):
    """Wait for miners to process transactions"""
    log(f"Waiting {seconds} seconds for miners to process...")
    for i in range(seconds):
        time.sleep(1)
        if (i + 1) % 5 == 0:
            print(f"  ... {i + 1}s elapsed")

def get_blockchain_info():
    """Get current blockchain information"""
    try:
        response = requests.post(f"{NODE_URL}/get_blockchain", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                "length": data.get("length", 0),
                "blocks": data.get("blockchain", [])
            }
        return None
    except Exception as e:
        log(f"[ERROR] getting blockchain: {e}")
        return None

def print_balances():
    """Print all wallet balances"""
    log("=== Current Balances ===")
    for name, wallet in WALLETS.items():
        balance = get_balance(wallet["address"])
        if balance is not None:
            log(f"  {name:10s}: {balance:8.2f} PHN ({wallet['address'][:20]}...)")
        else:
            log(f"  {name:10s}: ERROR")

def check_recent_transactions(num_blocks=5):
    """Check recent blocks for transactions"""
    log(f"=== Checking last {num_blocks} blocks for transactions ===")
    
    blockchain_info = get_blockchain_info()
    if not blockchain_info:
        log("[ERROR] Could not fetch blockchain")
        return
    
    blocks = blockchain_info["blocks"]
    recent_blocks = blocks[-num_blocks:] if len(blocks) >= num_blocks else blocks
    
    for block in recent_blocks:
        block_index = block.get("index", "?")
        transactions = block.get("transactions", [])
        log(f"Block #{block_index}: {len(transactions)} transaction(s)")
        
        for tx in transactions:
            sender = tx.get("sender", "?")
            recipient = tx.get("recipient", "?")
            amount = tx.get("amount", 0)
            
            if "coinbase" in sender.lower() or sender == "0":
                log(f"  [OK] COINBASE -> {recipient[:20]}... | {amount} PHN (mining reward)")
            else:
                log(f"  [OK] {sender[:20]}... -> {recipient[:20]}... | {amount} PHN")

def main():
    """Run comprehensive transaction tests"""
    log("="*60)
    log("PHN Blockchain Transaction Testing")
    log("="*60)
    
    # Test 1: Check initial balances
    log("\n### TEST 1: Initial Balance Check ###")
    print_balances()
    
    # Test 2: Send transaction from FUND to MINER1
    log("\n### TEST 2: Send 1 PHN from FUND to MINER1 ###")
    txid1 = send_transaction("FUND", "MINER1", 1.0, 0.02)
    
    if txid1:
        wait_for_mining(15)
        log("\nChecking if transaction was mined...")
        check_recent_transactions(5)
        log("\nBalances after transaction:")
        print_balances()
    
    # Test 3: Send transaction from MINER1 back to FUND
    log("\n### TEST 3: Send 1 PHN from MINER1 back to FUND ###")
    time.sleep(2)  # Small delay between transactions
    txid2 = send_transaction("MINER1", "FUND", 1.0, 0.02)
    
    if txid2:
        wait_for_mining(15)
        log("\nChecking if transaction was mined...")
        check_recent_transactions(5)
        log("\nBalances after return transaction:")
        print_balances()
    
    # Test 4: Send transaction from MINER1 to MINER2
    log("\n### TEST 4: Send 1 PHN from MINER1 to MINER2 ###")
    time.sleep(2)
    txid3 = send_transaction("MINER1", "MINER2", 1.0, 0.02)
    
    if txid3:
        wait_for_mining(15)
        log("\nChecking if transaction was mined...")
        check_recent_transactions(5)
        log("\nBalances after MINER1->MINER2 transaction:")
        print_balances()
    
    # Final summary
    log("\n" + "="*60)
    log("TEST SUMMARY")
    log("="*60)
    check_recent_transactions(10)
    log("\nFinal Balances:")
    print_balances()
    
    blockchain_info = get_blockchain_info()
    if blockchain_info:
        log(f"\nBlockchain height: {blockchain_info['length']} blocks")
    
    log("\n[OK] All transaction tests completed!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("\n\nTest interrupted by user")
    except Exception as e:
        log(f"\n[ERROR] Test failed with error: {e}")
        import traceback
        traceback.print_exc()
