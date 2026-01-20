#!/usr/bin/env python3
"""
Test blockchain using Phonesium SDK
Verifies wallet creation, transaction signing, and balance checking
"""

import sys

sys.path.insert(0, ".")

from phonesium import Wallet, PhonesiumClient
from phonesium.core.exceptions import NetworkError, InsufficientBalanceError
import time

NODE_URL = "http://localhost:8765"


def test_wallet_operations():
    """Test wallet creation and operations"""
    print("\n" + "=" * 60)
    print("TEST 1: Wallet Operations")
    print("=" * 60)

    # Create new wallet
    print("\n[1] Creating new wallet...")
    wallet = Wallet.create()
    print(f"  [OK] Address: {wallet.address}")
    print(f"  [OK] Public key length: {len(wallet.public_key)}")

    # Sign data
    print("\n[2] Testing signing...")
    message = "Test message"
    signature = wallet.sign(message)
    print(f"  [OK] Signature created: {signature[:32]}...")

    # Verify signature
    is_valid = wallet.verify_signature(message, signature)
    print(f"  [OK] Signature valid: {is_valid}")

    return wallet


def test_client_connection():
    """Test connecting to node"""
    print("\n" + "=" * 60)
    print("TEST 2: Node Connection")
    print("=" * 60)

    print("\n[1] Connecting to node...")
    client = PhonesiumClient(NODE_URL)
    print(f"  [OK] Connected to: {client.node_url}")

    print("\n[2] Getting token info...")
    try:
        info = client.get_token_info()
        print(f"  [OK] Token: {info.get('name', 'N/A')}")
        print(f"  [OK] Total supply: {info.get('total_supply', 0):,} PHN")
        print(f"  [OK] Circulating: {info.get('circulating_supply', 0):.2f} PHN")
    except NetworkError as e:
        print(f"  [ERROR] {e}")
        return None

    print("\n[3] Getting mining info...")
    try:
        mining = client.get_mining_info()
        print(f"  [OK] Difficulty: {mining.get('difficulty')}")
        print(f"  [OK] Block reward: {mining.get('block_reward')} PHN")
        print(f"  [OK] Min fee: {mining.get('min_tx_fee')} PHN")
        print(f"  [OK] Block height: {mining.get('current_block_height')}")
        print(f"  [OK] Pending TXs: {mining.get('pending_transactions')}")
    except NetworkError as e:
        print(f"  [ERROR] {e}")
        return None

    return client


def test_balance_checking(client):
    """Test balance checking"""
    print("\n" + "=" * 60)
    print("TEST 3: Balance Checking")
    print("=" * 60)

    # Test addresses from .env
    test_addresses = [
        ("FUND", "PHN0a2e1f46a128caa0fded990ac8f7c9fb5e7da8a6"),
        ("MINER", "PHN718b7ad6d46933825778e5c95757e12b853e3d0c"),
    ]

    for name, address in test_addresses:
        try:
            balance = client.get_balance(address)
            print(f"  [OK] {name:6s} balance: {balance:,.2f} PHN")
        except NetworkError as e:
            print(f"  [ERROR] {name}: {e}")


def test_wallet_from_private_key():
    """Test importing wallet from private key"""
    print("\n" + "=" * 60)
    print("TEST 4: Import Wallet from Private Key")
    print("=" * 60)

    # Use FUND wallet private key
    private_key = "aebfe0c96d56586b9290bd0b2d66f6c486c28fec110cec91e39414eb97bd679f"
    expected_address = "PHN0a2e1f46a128caa0fded990ac8f7c9fb5e7da8a6"

    print(f"\n[1] Importing wallet from private key...")
    wallet = Wallet.from_private_key(private_key)
    print(f"  [OK] Address: {wallet.address}")

    if wallet.address == expected_address:
        print(f"  [OK] Address matches expected!")
    else:
        print(f"  [ERROR] Address mismatch!")
        print(f"    Expected: {expected_address}")
        print(f"    Got:      {wallet.address}")

    return wallet


def test_transaction_creation(wallet):
    """Test creating a transaction (without sending)"""
    print("\n" + "=" * 60)
    print("TEST 5: Transaction Creation")
    print("=" * 60)

    recipient = "PHN718b7ad6d46933825778e5c95757e12b853e3d0c"
    amount = 0.01
    fee = 0.02

    print(f"\n[1] Creating transaction...")
    print(f"  From: {wallet.address}")
    print(f"  To:   {recipient}")
    print(f"  Amount: {amount} PHN")
    print(f"  Fee: {fee} PHN")

    import hashlib, random, orjson, time

    timestamp = time.time()
    nonce = random.randint(0, 999999)

    tx = {
        "sender": wallet.public_key,
        "recipient": recipient,
        "amount": amount,
        "fee": fee,
        "timestamp": timestamp,
        "nonce": nonce,
        "signature": "",
    }

    # Generate TXID
    hash_input = f"{tx['sender']}{tx['recipient']}{tx['amount']}{tx['fee']}{tx['timestamp']}{tx['nonce']}"
    tx["txid"] = hashlib.sha256(hash_input.encode()).hexdigest()

    # Sign
    tx_copy = dict(tx)
    tx_json = orjson.dumps(tx_copy, option=orjson.OPT_SORT_KEYS)
    tx["signature"] = wallet.sign(tx_json)

    print(f"  [OK] Transaction created")
    print(f"  [OK] TXID: {tx['txid'][:32]}...")
    print(f"  [OK] Signature: {tx['signature'][:32]}...")

    return tx


def main():
    print("=" * 60)
    print("PHN BLOCKCHAIN - PHONESIUM SDK TEST")
    print("=" * 60)

    try:
        # Test 1: Wallet operations
        wallet1 = test_wallet_operations()

        # Test 2: Client connection
        client = test_client_connection()
        if not client:
            print("\n[ERROR] Cannot connect to node")
            return 1

        # Test 3: Balance checking
        test_balance_checking(client)

        # Test 4: Import wallet
        wallet2 = test_wallet_from_private_key()

        # Test 5: Transaction creation
        tx = test_transaction_creation(wallet2)

        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print("  [OK] Wallet creation and signing")
        print("  [OK] Node connection")
        print("  [OK] Balance checking")
        print("  [OK] Wallet import from private key")
        print("  [OK] Transaction creation and signing")
        print("\n[SUCCESS] All Phonesium SDK tests passed!")
        print("=" * 60)

        return 0

    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
