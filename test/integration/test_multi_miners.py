#!/usr/bin/env python3
"""
PHN Network - Multi-Miner Test Script
Tests PoUV (Proof of Universal Validation) with 10 miners
Tests fault tolerance (miners dropping out)
"""

import subprocess
import time
import sys
import os
import hashlib
from pathlib import Path

# Add phonesium to path
sys.path.insert(0, str(Path(__file__).parent))

from phonesium import Wallet

NODE_URL = "http://localhost:8765"
NUM_MINERS = 10


def create_test_wallets(num_wallets=10):
    """Create 10 test wallets for miners"""
    print(f"\n{'=' * 70}")
    print(f"CREATING {num_wallets} TEST MINER WALLETS")
    print(f"{'=' * 70}\n")

    wallets = []
    for i in range(1, num_wallets + 1):
        # Create wallet
        wallet = Wallet()

        # Save to file
        wallet_dir = Path(__file__).parent / "test" / f"miner{i}"
        wallet_dir.mkdir(parents=True, exist_ok=True)

        wallet_file = wallet_dir / "wallet.txt"
        with open(wallet_file, "w") as f:
            f.write(f"ADDRESS={wallet.address}\n")
            f.write(f"PRIVATE_KEY={wallet.private_key}\n")
            f.write(f"PUBLIC_KEY={wallet.public_key}\n")

        wallets.append(
            {
                "number": i,
                "address": wallet.address,
                "private_key": wallet.private_key,
                "public_key": wallet.public_key,
                "wallet_file": str(wallet_file),
            }
        )

        print(f"[Miner {i:2d}] {wallet.address}")

    print(f"\n{'=' * 70}")
    print(f"All {num_wallets} wallets created and saved")
    print(f"{'=' * 70}\n")

    return wallets


def start_node():
    """Start the blockchain node"""
    print("\n[*] Starting PHN Network Node...")
    node_process = subprocess.Popen(
        [sys.executable, "-m", "app.main"],
        cwd=Path(__file__).parent,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    # Wait for node to start
    print("[*] Waiting for node to initialize (10 seconds)...")
    time.sleep(10)

    return node_process


def start_miner(miner_info, log_file):
    """Start a single miner process"""
    env = os.environ.copy()
    env["NODE_URL"] = NODE_URL
    env["MINER_ADDRESS"] = miner_info["address"]

    miner_process = subprocess.Popen(
        [sys.executable, "user/cli/miner.py"],
        cwd=Path(__file__).parent,
        env=env,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    return miner_process


def start_all_miners(wallets):
    """Start all miner processes"""
    print(f"\n{'=' * 70}")
    print(f"STARTING {len(wallets)} MINERS")
    print(f"{'=' * 70}\n")

    miner_processes = []
    logs_dir = Path(__file__).parent / "test_logs"
    logs_dir.mkdir(exist_ok=True)

    for wallet in wallets:
        log_file_path = logs_dir / f"miner{wallet['number']}.log"
        log_file = open(log_file_path, "w")

        process = start_miner(wallet, log_file)
        miner_processes.append(
            {
                "process": process,
                "wallet": wallet,
                "log_file": log_file,
                "log_path": str(log_file_path),
            }
        )

        print(
            f"[Miner {wallet['number']:2d}] Started (PID: {process.pid}) - Log: {log_file_path.name}"
        )
        time.sleep(0.5)  # Stagger starts

    print(f"\n{'=' * 70}")
    print(f"All {len(wallets)} miners started")
    print(f"{'=' * 70}\n")

    return miner_processes


def monitor_mining(miner_processes, duration=60):
    """Monitor mining activity"""
    print(f"\n{'=' * 70}")
    print(f"MONITORING MINING ACTIVITY ({duration}s)")
    print(f"{'=' * 70}\n")

    start_time = time.time()

    try:
        while time.time() - start_time < duration:
            elapsed = int(time.time() - start_time)
            remaining = duration - elapsed

            # Check which miners are still running
            active_count = sum(
                1 for mp in miner_processes if mp["process"].poll() is None
            )

            print(
                f"[{elapsed:3d}s] Active miners: {active_count}/{len(miner_processes)} | Time remaining: {remaining}s",
                end="\r",
            )
            time.sleep(1)

        print()  # New line after monitoring

    except KeyboardInterrupt:
        print("\n[!] Monitoring interrupted by user")


def test_fault_tolerance(miner_processes):
    """Test fault tolerance by killing random miners"""
    print(f"\n{'=' * 70}")
    print(f"TESTING FAULT TOLERANCE")
    print(f"{'=' * 70}\n")

    import random

    # Kill 3 random miners
    miners_to_kill = random.sample(miner_processes, 3)

    for mp in miners_to_kill:
        print(f"[*] Killing Miner {mp['wallet']['number']} (PID: {mp['process'].pid})")
        mp["process"].terminate()
        mp["process"].wait(timeout=5)
        mp["log_file"].close()

    print(f"\n[*] Killed 3 miners. Remaining: {len(miner_processes) - 3}")
    print("[*] Monitoring remaining miners for 30 seconds...\n")

    # Monitor for 30 more seconds
    monitor_mining(miner_processes, duration=30)

    # Count survivors
    survivors = sum(1 for mp in miner_processes if mp["process"].poll() is None)
    print(
        f"\n[[OK]] Fault tolerance test complete. {survivors}/{len(miner_processes)} miners still active"
    )


def cleanup(node_process, miner_processes):
    """Clean up all processes"""
    print(f"\n{'=' * 70}")
    print("CLEANING UP")
    print(f"{'=' * 70}\n")

    # Stop all miners
    for mp in miner_processes:
        if mp["process"].poll() is None:
            print(
                f"[*] Stopping Miner {mp['wallet']['number']} (PID: {mp['process'].pid})"
            )
            mp["process"].terminate()
            try:
                mp["process"].wait(timeout=5)
            except subprocess.TimeoutExpired:
                mp["process"].kill()

        mp["log_file"].close()

    # Stop node
    if node_process and node_process.poll() is None:
        print(f"[*] Stopping Node (PID: {node_process.pid})")
        node_process.terminate()
        try:
            node_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            node_process.kill()

    print("\n[[OK]] All processes stopped")


def print_summary(miner_processes):
    """Print test summary"""
    print(f"\n{'=' * 70}")
    print("TEST SUMMARY")
    print(f"{'=' * 70}\n")

    print(f"Total miners started: {len(miner_processes)}")

    active = sum(1 for mp in miner_processes if mp["process"].poll() is None)
    stopped = len(miner_processes) - active

    print(f"Active miners: {active}")
    print(f"Stopped miners: {stopped}")

    print(f"\nLog files saved in: test_logs/")
    print(f"Wallet files saved in: test/miner*/wallet.txt")

    print(f"\n{'=' * 70}\n")


def main():
    """Main test orchestration"""
    print(f"\n{'=' * 70}")
    print("PHN NETWORK - MULTI-MINER TEST")
    print("Testing PoUV & Fault Tolerance")
    print(f"{'=' * 70}\n")

    node_process = None
    miner_processes = []

    try:
        # Step 1: Create wallets
        wallets = create_test_wallets(NUM_MINERS)

        # Step 2: Start node
        node_process = start_node()

        # Step 3: Start all miners
        miner_processes = start_all_miners(wallets)

        # Step 4: Monitor mining (60 seconds)
        print("[*] Letting miners compete for 60 seconds...")
        monitor_mining(miner_processes, duration=60)

        # Step 5: Test fault tolerance
        test_fault_tolerance(miner_processes)

        # Step 6: Print summary
        print_summary(miner_processes)

    except KeyboardInterrupt:
        print("\n[!] Test interrupted by user")

    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback

        traceback.print_exc()

    finally:
        # Always cleanup
        cleanup(node_process, miner_processes)


if __name__ == "__main__":
    main()
