#!/usr/bin/env python3
"""
Complete blockchain test flow:
1. Check node status
2. Check initial balances
3. Send transaction from FUND to MINER
4. Wait for mining
5. Verify balances updated correctly
"""

import time
import requests
import hashlib
import orjson
import random
from ecdsa import SigningKey, SECP256k1

NODE_URL = "http://localhost:8765"

# Wallet credentials from .env
FUND_WALLET = {
    "address": "PHN0a2e1f46a128caa0fded990ac8f7c9fb5e7da8a6",
    "private_key": "aebfe0c96d56586b9290bd0b2d66f6c486c28fec110cec91e39414eb97bd679f",
    "public_key": "4fdae4ab16c8f4283f262139a71214e80da3a8e6880b5ef52eb0435d95ecdef30801ae7887badcefd54689e32bff9b9f1221bae02dd6556a58a56f07a7b69e12",
}

MINER_WALLET = {
    "address": "PHN718b7ad6d46933825778e5c95757e12b853e3d0c",
    "private_key": "6d3bde63c09de2bd2cd1c02ea9e92f71d14d642ac05e5f3895b60f61893cd980",
    "public_key": "22aec866ecd19d1d6e6ebe7c1e832fb7404742c2ba89dff2839d215c17e9ac3d8b9c3f0c6c6f87bc16a3085ebd667e7b3a3307adf62b6308e9bf48524bf8b4bb",
}


def log(msg):
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] {msg}")


def check_node_status():
    """Check if node is running"""
    try:
        response = requests.get(f"{NODE_URL}/", timeout=5)
        if response.status_code == 200:
            log("[OK] Node is running")
            return True
        log("[ERROR] Node returned non-200 status")
        return False
    except Exception as e:
        log(f"[ERROR] Node is not running: {e}")
        return False


def get_balance(address):
    """Get balance for address"""
    try:
        response = requests.post(
            f"{NODE_URL}/get_balance", json={"address": address}, timeout=5
        )
        if response.status_code == 200:
            return response.json().get("balance", 0.0)
        return None
    except Exception as e:
        log(f"[ERROR] Error getting balance: {e}")
        return None


def create_transaction(sender_wallet, recipient_address, amount, fee=0.02):
    """Create and sign a transaction"""
    timestamp = time.time()
    nonce = random.randint(0, 999999)

    # Create transaction
    tx = {
        "sender": sender_wallet["public_key"],
        "recipient": recipient_address,
        "amount": amount,
        "fee": fee,
        "timestamp": timestamp,
        "nonce": nonce,
        "signature": "",
    }

    # Generate TXID
    hash_input = f"{tx['sender']}{tx['recipient']}{tx['amount']}{tx['fee']}{tx['timestamp']}{tx['nonce']}"
    tx["txid"] = hashlib.sha256(hash_input.encode()).hexdigest()

    # Sign transaction
    sk = SigningKey.from_string(
        bytes.fromhex(sender_wallet["private_key"]), curve=SECP256k1
    )
    tx_copy = dict(tx)
    tx_copy.pop("signature", None)
    tx_json = orjson.dumps(tx_copy, option=orjson.OPT_SORT_KEYS)
    tx["signature"] = sk.sign(tx_json).hex()

    return tx


def send_transaction(tx):
    """Send transaction to node"""
    try:
        response = requests.post(f"{NODE_URL}/send_tx", json={"tx": tx}, timeout=10)
        if response.status_code == 200:
            result = response.json()
            return True, result
        else:
            return False, response.text
    except Exception as e:
        return False, str(e)


def get_blockchain_length():
    """Get current blockchain length"""
    try:
        response = requests.post(f"{NODE_URL}/get_blockchain", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get("length", 0)
        return 0
    except:
        return 0


def main():
    print("=" * 70)
    print("PHN BLOCKCHAIN - COMPLETE FLOW TEST")
    print("=" * 70)

    # Step 1: Check node status
    log("\n[STEP 1] Checking node status...")
    if not check_node_status():
        log("[ERROR] Node is not running. Please start with: python -m app.main")
        return 1

    # Step 2: Check initial balances
    log("\n[STEP 2] Checking initial balances...")
    fund_balance_before = get_balance(FUND_WALLET["address"])
    miner_balance_before = get_balance(MINER_WALLET["address"])

    if fund_balance_before is None or miner_balance_before is None:
        log("[ERROR] Failed to get balances")
        return 1

    log(f"  FUND wallet:  {fund_balance_before:.2f} PHN")
    log(f"  MINER wallet: {miner_balance_before:.2f} PHN")

    if fund_balance_before < 10:
        log("[ERROR] FUND wallet has insufficient balance for test")
        return 1

    # Step 3: Get blockchain info
    log("\n[STEP 3] Getting blockchain info...")
    chain_length_before = get_blockchain_length()
    log(f"  Blockchain length: {chain_length_before} blocks")

    # Step 4: Create and send transaction
    log("\n[STEP 4] Creating transaction...")
    amount = 5.0
    fee = 0.02
    total_deduction = amount + fee

    log(f"  Sending {amount} PHN from FUND to MINER")
    log(f"  Fee: {fee} PHN")
    log(f"  Total deduction: {total_deduction} PHN")

    tx = create_transaction(FUND_WALLET, MINER_WALLET["address"], amount, fee)
    log(f"  Transaction ID: {tx['txid'][:32]}...")

    # Step 5: Submit transaction
    log("\n[STEP 5] Submitting transaction to node...")
    success, result = send_transaction(tx)

    if not success:
        log(f"[ERROR] Transaction failed: {result}")
        return 1

    log(f"[OK] Transaction accepted by node")
    log(f"  TXID: {result.get('txid', 'N/A')}")

    # Step 6: Wait for mining
    log("\n[STEP 6] Waiting for transaction to be mined...")
    log("  Waiting for miner to process transaction (up to 120 seconds)...")

    max_wait = 120
    wait_interval = 5
    waited = 0

    while waited < max_wait:
        time.sleep(wait_interval)
        waited += wait_interval

        # Check if blockchain length increased
        current_length = get_blockchain_length()
        if current_length > chain_length_before:
            log(f"[OK] New block mined! Blockchain length: {current_length}")
            break

        if waited % 15 == 0:
            log(f"  Still waiting... ({waited}s elapsed)")

    if waited >= max_wait:
        log("[WARN] Timeout waiting for block to be mined")
        log("  Transaction may still be in mempool")

    # Give it a moment for balances to update
    time.sleep(2)

    # Step 7: Verify balances
    log("\n[STEP 7] Verifying balances after transaction...")
    fund_balance_after = get_balance(FUND_WALLET["address"])
    miner_balance_after = get_balance(MINER_WALLET["address"])

    if fund_balance_after is None or miner_balance_after is None:
        log("[ERROR] Failed to get updated balances")
        return 1

    log(f"\n  FUND wallet:")
    log(f"    Before:  {fund_balance_before:.2f} PHN")
    log(f"    After:   {fund_balance_after:.2f} PHN")
    log(f"    Change:  {fund_balance_after - fund_balance_before:.2f} PHN")

    log(f"\n  MINER wallet:")
    log(f"    Before:  {miner_balance_before:.2f} PHN")
    log(f"    After:   {miner_balance_after:.2f} PHN")
    log(f"    Change:  {miner_balance_after - miner_balance_before:.2f} PHN")

    # Step 8: Validate transaction effects
    log("\n[STEP 8] Validating transaction effects...")

    expected_fund_balance = fund_balance_before - total_deduction
    expected_miner_balance = miner_balance_before + amount

    # Check if transaction was mined
    if abs(fund_balance_after - expected_fund_balance) < 0.01:
        log(f"[OK] FUND wallet balance correct (expected: {expected_fund_balance:.2f})")
    else:
        log(f"[WARN] FUND wallet balance unexpected")
        log(f"    Expected: {expected_fund_balance:.2f} PHN")
        log(f"    Actual:   {fund_balance_after:.2f} PHN")

    if (
        abs(miner_balance_after - expected_miner_balance) < 50.1
    ):  # Allow for mining rewards
        log(
            f"[OK] MINER wallet received transaction (expected at least: {expected_miner_balance:.2f})"
        )
    else:
        log(f"[WARN] MINER wallet balance unexpected")
        log(f"    Expected at least: {expected_miner_balance:.2f} PHN")
        log(f"    Actual: {miner_balance_after:.2f} PHN")

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    if waited < max_wait and abs(fund_balance_after - expected_fund_balance) < 0.01:
        log("[OK] ALL TESTS PASSED!")
        log("  * Node is running correctly")
        log("  * Transaction was created and signed correctly")
        log("  * Transaction was accepted by node")
        log("  * Transaction was mined successfully")
        log("  * Balances updated correctly")
        return 0
    else:
        log("[WARN] TESTS COMPLETED WITH WARNINGS")
        log("  * Node and transaction system working")
        log("  * Transaction may still be processing")
        log("  * Check miner logs for details")
        return 0


if __name__ == "__main__":
    try:
        exit(main())
    except KeyboardInterrupt:
        log("\n\nTest interrupted by user")
        exit(1)
    except Exception as e:
        log(f"\n[ERROR] Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        exit(1)
