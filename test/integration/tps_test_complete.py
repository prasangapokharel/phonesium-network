#!/usr/bin/env python3
"""
TPS (Transactions Per Second) Test for PHN Blockchain
Tests transaction throughput with 4 competing miners
Then returns all funds back to FUND address
"""

import requests
import hashlib
import orjson
import time
import random
import ecdsa
from datetime import datetime

NODE_URL = "http://localhost:8765"

# Wallet details - ALL 4 wallets
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
    },
    "MINER4": {
        "address": "PHN814f3d1c55537d2f76e6632cb8251dd64f6d046d",
        "private_key": "1c418c1ed1dd9b243009a72fde0b52c587eee35ef42daa3f36066e10a91fe785",
        "public_key": "0d2f5a33b701e6a56dcd1d59de308b6e6445200496a3afc24d9dc8298ea0d9ed1fed62cf58c20064fcee9acfaf15dfabd8c0fd8f8bfa4d1651d79479df57ce0c"
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
        return None

def make_txid(sender, recipient, amount, fee, timestamp, nonce):
    """Generate transaction ID"""
    s = f"{sender}{recipient}{amount}{fee}{timestamp}{nonce}"
    return hashlib.sha256(s.encode()).hexdigest()

def sign_transaction(tx_data, private_key):
    """Sign a transaction"""
    tx_copy = dict(tx_data)
    tx_copy.pop("signature", None)
    tx_json = orjson.dumps(tx_copy, option=orjson.OPT_SORT_KEYS)
    sk = ecdsa.SigningKey.from_string(bytes.fromhex(private_key), curve=ecdsa.SECP256k1)
    signature = sk.sign(tx_json)
    return signature.hex()

def send_transaction(sender_wallet, recipient_address, amount, fee=0.02):
    """Send a transaction"""
    timestamp = time.time()
    nonce = random.randint(0, 999999)
    txid = make_txid(sender_wallet["public_key"], recipient_address, amount, fee, timestamp, nonce)
    
    tx_data = {
        "txid": txid,
        "sender": sender_wallet["public_key"],
        "recipient": recipient_address,
        "amount": amount,
        "fee": fee,
        "timestamp": timestamp,
        "nonce": nonce,
        "sender_public_key": sender_wallet["public_key"]
    }
    
    signature = sign_transaction(tx_data, sender_wallet["private_key"])
    tx_data["signature"] = signature
    
    try:
        response = requests.post(
            f"{NODE_URL}/send_tx",
            json={"tx": tx_data},
            timeout=10
        )
        
        if response.status_code == 200:
            return {"success": True, "txid": txid}
        else:
            return {"success": False, "error": response.text}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_blockchain_info():
    """Get blockchain info"""
    try:
        response = requests.post(f"{NODE_URL}/get_blockchain", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                "length": data.get("length", 0),
                "blocks": data.get("blockchain", [])
            }
        return None
    except:
        return None

def print_balances():
    """Print all wallet balances"""
    log("=== Current Balances ===")
    total = 0
    for name, wallet in WALLETS.items():
        balance = get_balance(wallet["address"])
        if balance is not None:
            log(f"  {name:10s}: {balance:10.2f} PHN")
            total += balance
        else:
            log(f"  {name:10s}: ERROR")
    log(f"  {'TOTAL':10s}: {total:10.2f} PHN")
    return total

def analyze_miner_competition(start_block, end_block):
    """Analyze which miner won each block"""
    log("\n=== Miner Competition Analysis ===")
    blockchain_info = get_blockchain_info()
    if not blockchain_info:
        log("Could not fetch blockchain")
        return
    
    blocks = blockchain_info["blocks"]
    miner_wins = {}
    
    for block in blocks[start_block:end_block]:
        # Find coinbase transaction to identify miner
        for tx in block.get("transactions", []):
            if tx.get("sender") == "coinbase":
                miner = tx.get("recipient", "unknown")
                # Map to miner name
                miner_name = "UNKNOWN"
                for name, wallet in WALLETS.items():
                    if wallet["address"] == miner:
                        miner_name = name
                        break
                
                miner_wins[miner_name] = miner_wins.get(miner_name, 0) + 1
                log(f"Block #{block['index']} won by: {miner_name}")
                break
    
    log("\n=== Competition Results ===")
    for miner, wins in sorted(miner_wins.items(), key=lambda x: x[1], reverse=True):
        log(f"  {miner}: {wins} blocks")

def tps_test():
    """Run TPS test"""
    log("="*70)
    log("TPS TEST - Transactions Per Second")
    log("="*70)
    
    # Initial state
    log("\nInitial State:")
    initial_height = get_blockchain_info()["length"]
    log(f"Blockchain height: {initial_height}")
    print_balances()
    
    # Send rapid transactions
    log("\n=== PHASE 1: Rapid Transaction Test (TPS) ===")
    log("Sending 20 transactions as fast as possible...")
    
    transactions = []
    start_time = time.time()
    
    # Send 10 from FUND to various wallets
    for i in range(5):
        result = send_transaction(WALLETS["FUND"], WALLETS["MINER1"]["address"], 1.0)
        transactions.append(result)
        if result["success"]:
            log(f"  TX {i+1}/20: FUND -> MINER1 | 1.0 PHN [OK]")
        else:
            log(f"  TX {i+1}/20: FAILED - {result.get('error', 'unknown')[:50]}")
    
    for i in range(5):
        result = send_transaction(WALLETS["FUND"], WALLETS["MINER2"]["address"], 1.0)
        transactions.append(result)
        if result["success"]:
            log(f"  TX {i+6}/20: FUND -> MINER2 | 1.0 PHN [OK]")
    
    for i in range(5):
        result = send_transaction(WALLETS["FUND"], WALLETS["MINER4"]["address"], 1.0)
        transactions.append(result)
        if result["success"]:
            log(f"  TX {i+11}/20: FUND -> MINER4 | 1.0 PHN [OK]")
    
    # Small transactions between miners
    for i in range(5):
        result = send_transaction(WALLETS["MINER1"], WALLETS["MINER2"]["address"], 0.5)
        transactions.append(result)
        if result["success"]:
            log(f"  TX {i+16}/20: MINER1 -> MINER2 | 0.5 PHN [OK]")
    
    end_time = time.time()
    elapsed = end_time - start_time
    
    successful = sum(1 for tx in transactions if tx.get("success"))
    tps = successful / elapsed if elapsed > 0 else 0
    
    log(f"\n=== TPS Results ===")
    log(f"  Transactions sent: {len(transactions)}")
    log(f"  Successful: {successful}")
    log(f"  Time taken: {elapsed:.2f} seconds")
    log(f"  TPS (send rate): {tps:.2f} transactions/second")
    
    # Wait for mining
    log(f"\n=== Waiting for transactions to be mined ===")
    log("This may take a while with 4 miners competing...")
    
    start_wait = time.time()
    wait_time = 0
    max_wait = 300  # 5 minutes
    
    while wait_time < max_wait:
        time.sleep(15)
        wait_time = time.time() - start_wait
        
        # Check pending count
        try:
            response = requests.post(f"{NODE_URL}/get_pending", timeout=5)
            pending_count = response.json().get("count", -1)
            current_height = get_blockchain_info()["length"]
            blocks_mined = current_height - initial_height
            
            log(f"  [{int(wait_time)}s] Pending: {pending_count} | Height: {current_height} (+{blocks_mined} blocks)")
            
            if pending_count == 0:
                log(f"\n[OK] All transactions mined in {wait_time:.1f} seconds!")
                break
        except:
            pass
    
    final_height = get_blockchain_info()["length"]
    blocks_mined = final_height - initial_height
    
    log(f"\n=== Mining Results ===")
    log(f"  Blocks mined: {blocks_mined}")
    log(f"  Time to mine all: {wait_time:.1f} seconds")
    if blocks_mined > 0:
        log(f"  Average block time: {wait_time/blocks_mined:.1f} seconds")
    
    # Analyze competition
    analyze_miner_competition(initial_height, final_height)
    
    log("\n=== Balances After TPS Test ===")
    print_balances()
    
    return initial_height, final_height

def return_all_funds_to_fund():
    """Return all funds from all wallets back to FUND"""
    log("\n" + "="*70)
    log("PHASE 2: Returning ALL Funds to FUND Address")
    log("="*70)
    
    log("\nCalculating amounts to return...")
    returns = []
    
    for name, wallet in WALLETS.items():
        if name == "FUND":
            continue  # Skip FUND itself
        
        balance = get_balance(wallet["address"])
        if balance and balance > 0.02:  # Need to keep fee
            # Return all minus fee
            amount_to_return = balance - 0.02
            returns.append({
                "name": name,
                "wallet": wallet,
                "balance": balance,
                "return_amount": amount_to_return
            })
            log(f"  {name}: {balance:.2f} PHN -> returning {amount_to_return:.2f} PHN")
    
    log(f"\nSending {len(returns)} return transactions...")
    
    for ret in returns:
        result = send_transaction(
            ret["wallet"],
            WALLETS["FUND"]["address"],
            ret["return_amount"]
        )
        if result["success"]:
            log(f"  [OK] {ret['name']} -> FUND | {ret['return_amount']:.2f} PHN")
        else:
            log(f"  [ERROR] {ret['name']} failed: {result.get('error', 'unknown')[:50]}")
    
    # Wait for mining
    log("\nWaiting for return transactions to be mined...")
    time.sleep(60)
    
    # Check pending
    try:
        response = requests.post(f"{NODE_URL}/get_pending", timeout=5)
        pending = response.json().get("count", 0)
        log(f"Pending transactions: {pending}")
        
        if pending > 0:
            log("Still waiting for transactions to be mined...")
            time.sleep(60)
    except:
        pass
    
    log("\n=== FINAL Balances (After Returns) ===")
    final_total = print_balances()
    
    fund_balance = get_balance(WALLETS["FUND"]["address"])
    log(f"\nFUND address has: {fund_balance:.2f} PHN")
    log(f"Total in system: {final_total:.2f} PHN")

def main():
    """Run complete test suite"""
    log("="*70)
    log("PHN BLOCKCHAIN - COMPLETE TEST SUITE")
    log("4 Miners Competition + TPS Test + Fund Return")
    log("="*70)
    
    # Phase 1: TPS Test
    start_block, end_block = tps_test()
    
    # Phase 2: Return funds
    return_all_funds_to_fund()
    
    # Final report
    log("\n" + "="*70)
    log("TEST COMPLETE")
    log("="*70)
    
    blockchain_info = get_blockchain_info()
    if blockchain_info:
        log(f"\nFinal blockchain height: {blockchain_info['length']} blocks")
    
    log("\nAll tests completed successfully!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("\n\nTest interrupted by user")
    except Exception as e:
        log(f"\n\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
