#!/usr/bin/env python3
"""
PHN Network - Quick TPS Test
Fast TPS measurement (30 seconds)
"""

import sys
import time
import requests
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from phonesium import Wallet, PhonesiumClient

NODE_URL = "http://localhost:8765"


def print_header(title):
    print(f"\n{'=' * 70}")
    print(f"{title}")
    print(f"{'=' * 70}\n")


def main():
    print_header("PHN NETWORK - QUICK TPS TEST (30 seconds)")

    # Check node
    try:
        response = requests.get(f"{NODE_URL}/", timeout=5)
        if response.status_code != 200:
            print(f"[[FAIL]] Cannot connect to node at {NODE_URL}")
            print(f"[!] Start node: python -m app.main")
            return
        print(f"[[OK]] Node connected\n")
    except Exception as e:
        print(f"[[FAIL]] Cannot connect: {e}")
        return

    client = PhonesiumClient(NODE_URL)

    # Load FUND wallet
    import os
    from dotenv import load_dotenv

    load_dotenv()

    fund_wallet = Wallet()
    fund_wallet.private_key = os.getenv("FUND_PRIVATE_KEY")
    fund_wallet.public_key = os.getenv("FUND_PUBLIC_KEY")
    fund_wallet.address = os.getenv("FUND_ADDRESS")

    # Check balance
    response = requests.post(
        f"{NODE_URL}/get_balance", json={"address": fund_wallet.address}, timeout=5
    )
    balance = float(response.json().get("balance", 0))

    print(f"[*] FUND Balance: {balance:.2f} PHN")

    if balance < 10:
        print("[!] Low balance. Mine blocks first: python user/cli/miner.py")
        return

    # Create test wallets
    print(f"\n[*] Creating 50 test wallets...")
    recipients = []
    for i in range(50):
        wallet = Wallet()
        recipients.append(wallet.address)
    print(f"[[OK]] Created 50 wallets\n")

    # Test: Send 50 transactions as fast as possible
    print_header("SENDING 50 TRANSACTIONS")

    success = 0
    failed = 0
    response_times = []

    start_time = time.time()

    for i, recipient in enumerate(recipients):
        tx_start = time.time()

        try:
            tx_data = client.create_transaction(
                sender_private_key=fund_wallet.private_key,
                sender_public_key=fund_wallet.public_key,
                recipient_address=recipient,
                amount=0.1,
                fee=0.02,
            )

            response = requests.post(
                f"{NODE_URL}/add_transaction", json=tx_data, timeout=5
            )

            tx_time = time.time() - tx_start
            response_times.append(tx_time)

            if response.status_code == 200:
                success += 1
                print(
                    f"[{i + 1:2d}/50] [OK] Sent in {tx_time * 1000:.0f}ms | Success: {success}",
                    end="\r",
                )
            else:
                failed += 1
                print(
                    f"[{i + 1:2d}/50] [FAIL] Failed | Success: {success} Failed: {failed}",
                    end="\r",
                )

        except Exception as e:
            failed += 1
            print(
                f"[{i + 1:2d}/50] [FAIL] Error | Success: {success} Failed: {failed}",
                end="\r",
            )

    total_time = time.time() - start_time

    print()  # New line

    # Calculate TPS
    tps = success / total_time if total_time > 0 else 0
    avg_response = sum(response_times) / len(response_times) if response_times else 0

    # Results
    print_header("SUBMISSION TPS RESULTS")

    print(f"Total Sent:                  {success + failed}")
    print(f"Successful:                  {success}")
    print(f"Failed:                      {failed}")
    print(f"Success Rate:                {(success / (success + failed) * 100):.1f}%")
    print()
    print(f"Total Time:                  {total_time:.2f} seconds")
    print(f"Submission TPS:              {tps:.2f} TPS")
    print(f"Avg Response Time:           {avg_response * 1000:.2f} ms")

    # Check pending transactions
    time.sleep(1)
    response = requests.post(f"{NODE_URL}/get_pending", timeout=5)
    pending_count = len(response.json().get("pending_transactions", []))

    print()
    print(f"Pending Transactions:        {pending_count}")

    print_header(f"[OK] SUBMISSION TPS: {tps:.2f} TPS")

    # Mining TPS test (if miner running)
    print("\n[*] To measure MINING TPS (actual throughput):")
    print("    1. Start a miner: python user/cli/miner.py")
    print("    2. Wait 60 seconds")
    print("    3. Check how many transactions were included in blocks")
    print()
    print("[*] Mining TPS = (Transactions in blocks) / (Time in seconds)")
    print("[*] Note: Mining TPS is limited by block time and difficulty")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[!] Test interrupted")
