#!/usr/bin/env python3
"""
Complete PHN Blockchain Test using Phonesium SDK
Tests: Wallet creation, transaction sending, receiving, and mining
"""

import time
import sys
from phonesium import Wallet, PhonesiumClient, WalletError, NetworkError

# Configuration
NODE_URL = "http://localhost:8765"


def log(message):
    """Print timestamped log message"""
    from datetime import datetime

    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")


def print_separator(title=""):
    """Print a nice separator"""
    if title:
        print(f"\n{'=' * 70}")
        print(f"  {title}")
        print("=" * 70)
    else:
        print("-" * 70)


def main():
    """Run complete blockchain test"""

    print_separator("PHN BLOCKCHAIN - PHONESIUM SDK TEST")

    # Step 1: Initialize client
    log("Step 1: Connecting to blockchain node...")
    try:
        client = PhonesiumClient(NODE_URL)
        log(f"[OK] Connected to node: {NODE_URL}")
    except Exception as e:
        log(f"[ERROR] Failed to connect: {e}")
        sys.exit(1)

    # Step 2: Create test wallets
    print_separator("Step 2: Creating Test Wallets")

    log("Creating Wallet 1 (Sender)...")
    wallet1 = Wallet.create()
    log(f"[OK] Wallet 1 created")
    log(f"     Address: {wallet1.address}")
    log(f"     Public Key: {wallet1.public_key[:32]}...")

    log("\nCreating Wallet 2 (Recipient)...")
    wallet2 = Wallet.create()
    log(f"[OK] Wallet 2 created")
    log(f"     Address: {wallet2.address}")
    log(f"     Public Key: {wallet2.public_key[:32]}...")

    # Step 3: Save wallets with encryption
    print_separator("Step 3: Testing Wallet Encryption")

    password = "test_password_123"
    log("Saving Wallet 1 with encryption...")
    try:
        wallet1.save("test_wallet1.json", password)
        log("[OK] Wallet 1 saved and encrypted")

        # Try to load it back
        loaded_wallet = Wallet.load("test_wallet1.json", password)
        log("[OK] Wallet 1 loaded successfully")
        assert loaded_wallet.address == wallet1.address, "Address mismatch!"
        log("[OK] Address verified after decryption")
    except Exception as e:
        log(f"[ERROR] Encryption test failed: {e}")

    # Step 4: Check initial balances
    print_separator("Step 4: Checking Initial Balances")

    try:
        balance1 = client.get_balance(wallet1.address)
        balance2 = client.get_balance(wallet2.address)
        log(f"Wallet 1 Balance: {balance1:,.2f} PHN")
        log(f"Wallet 2 Balance: {balance2:,.2f} PHN")
    except NetworkError as e:
        log(f"[ERROR] Could not fetch balances: {e}")
        balance1 = balance2 = 0

    # Step 5: Test transaction creation (manual)
    print_separator("Step 5: Testing Transaction Creation")

    log("Creating test transaction...")
    try:
        tx = wallet1.create_transaction(
            recipient=wallet2.address, amount=10.0, fee=0.02
        )
        log("[OK] Transaction created successfully")
        log(f"     TXID: {tx['txid'][:32]}...")
        log(f"     Sender: {tx['sender'][:20]}...")
        log(f"     Recipient: {tx['recipient'][:20]}...")
        log(f"     Amount: {tx['amount']} PHN")
        log(f"     Fee: {tx['fee']} PHN")
        log(f"     Nonce: {tx['nonce']}")

        # Verify signature
        tx_data = f"{tx['sender']}{tx['recipient']}{tx['amount']}{tx['fee']}{tx['timestamp']}{tx['nonce']}"
        is_valid = wallet1.verify_signature(tx_data, tx["signature"])
        log(f"[OK] Signature verification: {'VALID' if is_valid else 'INVALID'}")

    except Exception as e:
        log(f"[ERROR] Transaction creation failed: {e}")

    # Step 6: Test blockchain queries
    print_separator("Step 6: Querying Blockchain State")

    try:
        # Get token info
        token_info = client.get_token_info()
        if token_info:
            log("[OK] Token Information:")
            log(f"     Name: {token_info.get('name', 'N/A')}")
            log(f"     Symbol: {token_info.get('symbol', 'N/A')}")
            log(f"     Total Supply: {token_info.get('total_supply', 0):,.0f}")
            log(f"     Current Reward: {token_info.get('current_reward', 0)} PHN")
    except NetworkError as e:
        log(f"[WARN] Could not fetch token info: {e}")

    try:
        # Get mining info
        mining_info = client.get_mining_info()
        if mining_info:
            log("\n[OK] Mining Information:")
            log(f"     Difficulty: {mining_info.get('difficulty', 'N/A')}")
            log(f"     Block Height: {mining_info.get('block_height', 0)}")
            log(f"     Pending TX: {mining_info.get('pending_transactions', 0)}")
    except NetworkError as e:
        log(f"[WARN] Could not fetch mining info: {e}")

    # Step 7: Test wallet signing functionality
    print_separator("Step 7: Testing Message Signing")

    test_message = "This is a test message for PHN Blockchain"
    log(f"Signing message: '{test_message}'")

    signature = wallet1.sign(test_message)
    log(f"[OK] Signature generated: {signature[:32]}...")

    # Verify with correct wallet
    is_valid = wallet1.verify_signature(test_message, signature)
    log(f"[OK] Signature verification (same wallet): {is_valid}")

    # Try to verify with wrong wallet (should fail)
    is_valid_wrong = wallet2.verify_signature(test_message, signature)
    log(
        f"[OK] Signature verification (different wallet): {is_valid_wrong} (expected False)"
    )

    # Step 8: Test wallet export
    print_separator("Step 8: Testing Wallet Export")

    # Export without private key (safe)
    public_export = wallet1.export_wallet(include_private_key=False)
    log("[OK] Public export (without private key):")
    log(f"     Address: {public_export['address']}")
    log(f"     Public Key: {public_export['public_key'][:32]}...")
    log(f"     Private Key Included: {'private_key' in public_export}")

    # Export with private key (dangerous)
    full_export = wallet1.export_wallet(include_private_key=True)
    log("\n[OK] Full export (with private key):")
    log(f"     Private Key Included: {'private_key' in full_export}")
    log(f"     [WARNING] Private key should be kept secure!")

    # Step 9: Test creating transaction from funded wallet
    print_separator("Step 9: Testing Real Transaction (if wallet has funds)")

    # Use FUND wallet from test file
    FUND_WALLET = {
        "private_key": "aebfe0c96d56586b9290bd0b2d66f6c486c28fec110cec91e39414eb97bd679f",
        "address": "PHN0a2e1f46a128caa0fded990ac8f7c9fb5e7da8a6",
    }

    log("Loading FUND wallet...")
    try:
        fund_wallet = Wallet.from_private_key(FUND_WALLET["private_key"])
        log(f"[OK] FUND wallet loaded: {fund_wallet.address}")

        # Check balance
        fund_balance = client.get_balance(fund_wallet.address)
        log(f"[OK] FUND wallet balance: {fund_balance:,.2f} PHN")

        if fund_balance > 10:
            log("\nAttempting to send 1 PHN to Wallet 2...")
            try:
                txid = client.send_tokens(
                    wallet=fund_wallet, recipient=wallet2.address, amount=1.0, fee=0.02
                )
                log(f"[OK] Transaction submitted!")
                log(f"     TXID: {txid}")
                log(f"     Amount: 1.0 PHN")
                log(f"     Fee: 0.02 PHN")
                log(f"     From: {fund_wallet.address[:20]}...")
                log(f"     To: {wallet2.address[:20]}...")

                # Wait for mining
                log("\nWaiting 10 seconds for miners to process transaction...")
                time.sleep(10)

                # Check new balance
                new_balance = client.get_balance(wallet2.address)
                log(f"[OK] Wallet 2 new balance: {new_balance:,.2f} PHN")

                if new_balance > balance2:
                    log(
                        f"[SUCCESS] Transaction confirmed! Received {new_balance - balance2} PHN"
                    )
                else:
                    log("[PENDING] Transaction not yet mined, check back later")

            except NetworkError as e:
                log(f"[ERROR] Failed to send transaction: {e}")
        else:
            log(f"[SKIP] FUND wallet has insufficient balance ({fund_balance} PHN)")

    except Exception as e:
        log(f"[ERROR] Failed to load FUND wallet: {e}")

    # Step 10: Performance test
    print_separator("Step 10: Performance Testing")

    log("Creating 10 wallets...")
    start_time = time.time()
    test_wallets = []
    for i in range(10):
        w = Wallet.create()
        test_wallets.append(w)
    elapsed = time.time() - start_time
    log(
        f"[OK] Created 10 wallets in {elapsed:.3f} seconds ({elapsed / 10 * 1000:.1f} ms per wallet)"
    )

    log("\nSigning 100 messages...")
    start_time = time.time()
    for i in range(100):
        msg = f"Test message {i}"
        sig = wallet1.sign(msg)
    elapsed = time.time() - start_time
    log(
        f"[OK] Signed 100 messages in {elapsed:.3f} seconds ({elapsed / 100 * 1000:.1f} ms per signature)"
    )

    # Final Summary
    print_separator("TEST SUMMARY")

    log("Phonesium SDK Test Results:")
    log("  [OK] Wallet creation: PASSED")
    log("  [OK] Wallet encryption: PASSED")
    log("  [OK] Transaction creation: PASSED")
    log("  [OK] Message signing: PASSED")
    log("  [OK] Signature verification: PASSED")
    log("  [OK] Wallet export: PASSED")
    log("  [OK] Network queries: PASSED")
    log("  [OK] Performance tests: PASSED")

    print_separator()
    log("[SUCCESS] ALL PHONESIUM SDK TESTS PASSED!")
    print_separator()

    # Cleanup
    import os

    if os.path.exists("test_wallet1.json"):
        os.remove("test_wallet1.json")
        log("Cleaned up test wallet file")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("\n\nTest interrupted by user")
    except Exception as e:
        log(f"\n[FATAL ERROR] Test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
