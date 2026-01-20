#!/usr/bin/env python3
"""
PHN Network - TPS Test with 1 PHN per transaction
Simple and straightforward test
"""

import sys
import time
import requests
import os
from pathlib import Path
from dotenv import load_dotenv
from ecdsa import SigningKey, SECP256k1

sys.path.insert(0, str(Path(__file__).parent))
from phonesium import Wallet, PhonesiumClient

NODE_URL = "http://localhost:8765"


def main():
    print("\n" + "=" * 70)
    print("PHN NETWORK - TPS TEST (1 PHN PER TRANSACTION)")
    print("=" * 70 + "\n")

    load_dotenv()

    # Use MINER wallet (has balance from mining)
    private_key = os.getenv("PRIVATE_KEY")
    address = os.getenv("MINER_ADDRESS")

    # Regenerate public key from private key
    sk = SigningKey.from_string(bytes.fromhex(private_key), curve=SECP256k1)
    public_key = sk.get_verifying_key().to_string().hex()

    sender_wallet = Wallet(private_key, public_key, address)
    client = PhonesiumClient(NODE_URL)

    # Check balance
    print("[*] Checking MINER wallet balance...")
    balance = client.get_balance(address)
    print(f"[OK] Balance: {balance:.2f} PHN\n")

    if balance < 50:
        print("[!] Low balance. Need at least 50 PHN")
        print("[!] Wait for more blocks to be mined")
        return

    # Create recipients
    num_tx = min(50, int(balance / 1.02) - 5)  # Leave buffer
    print(f"[*] Creating {num_tx} recipient wallets...")
    recipients = [Wallet.create() for _ in range(num_tx)]
    print(f"[OK] Created {num_tx} wallets\n")

    print("=" * 70)
    print(f"SENDING {num_tx} TRANSACTIONS (1 PHN EACH)")
    print("=" * 70)
    print(f"\nAmount: 1.0 PHN per transaction")
    print(f"Fee: 0.02 PHN per transaction")
    print(f"Total cost: {num_tx * 1.02:.2f} PHN\n")

    input("Press Enter to start TPS test...")

    print(f"\n[*] Sending {num_tx} transactions...\n")

    success = 0
    failed = 0
    times = []

    start = time.time()

    for i, recipient in enumerate(recipients):
        t0 = time.time()
        try:
            result = client.send_tokens(sender_wallet, recipient.address, 1.0, fee=0.02)
            t1 = time.time()
            times.append(t1 - t0)

            if result:
                success += 1
                print(
                    f"[{i + 1:2d}/{num_tx}] OK | {(t1 - t0) * 1000:.0f}ms | Success: {success}",
                    end="\r",
                )
            else:
                failed += 1
                print(
                    f"[{i + 1:2d}/{num_tx}] FAIL | Success: {success} Failed: {failed}",
                    end="\r",
                )
        except Exception as e:
            failed += 1
            if "Rate limit" in str(e):
                print(f"\n[!] Rate limited at transaction {i + 1}. Stopping test.")
                break
            print(f"[{i + 1:2d}/{num_tx}] ERROR | {str(e)[:30]}", end="\r")

    total_time = time.time() - start

    print("\n")

    # Results
    print("=" * 70)
    print("TPS TEST RESULTS")
    print("=" * 70)
    print(f"\nTotal Sent:                  {success + failed}")
    print(f"Successful:                  {success}")
    print(f"Failed:                      {failed}")
    print(f"Success Rate:                {(success / (success + failed) * 100):.1f}%")
    print(f"\nTotal Time:                  {total_time:.3f} seconds")
    print(f"Total PHN Sent:              {success * 1.0:.2f} PHN")
    print(f"Total Fees:                  {success * 0.02:.2f} PHN")
    print(f"\n" + "=" * 70)
    print(f"TRANSACTIONS PER SECOND:     {(success / total_time):.2f} TPS")
    print(f"=" * 70)

    if times:
        avg_time = sum(times) / len(times)
        print(f"\nAverage Response Time:       {avg_time * 1000:.2f} ms")
        print(f"Min Response Time:           {min(times) * 1000:.2f} ms")
        print(f"Max Response Time:           {max(times) * 1000:.2f} ms")

    # Check pending
    print(f"\n[*] Checking pending transactions...")
    pending = client.get_mempool()
    print(f"[OK] Pending transactions:   {len(pending)}")

    # Check new balance
    new_balance = client.get_balance(address)
    print(f"[OK] New balance:            {new_balance:.2f} PHN")
    print(f"[OK] Balance change:         -{(balance - new_balance):.2f} PHN")

    print("\n" + "=" * 70)
    print(f"TEST COMPLETE: {(success / total_time):.2f} TPS")
    print("=" * 70 + "\n")

    print("Summary:")
    print(f"  - Sent {success} transactions of 1.0 PHN each")
    print(f"  - Achieved {(success / total_time):.2f} transactions per second")
    print(f"  - Average {avg_time * 1000:.2f}ms per transaction")
    print(f"  - {len(pending)} transactions pending (waiting to be mined)")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted\n")
