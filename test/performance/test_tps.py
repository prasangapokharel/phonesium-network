#!/usr/bin/env python3
"""
PHN Network - TPS (Transactions Per Second) Benchmark
Measures the actual throughput of the blockchain system
"""

import sys
import time
import requests
import asyncio
import statistics
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add phonesium to path
sys.path.insert(0, str(Path(__file__).parent))

from phonesium import Wallet, PhonesiumClient

NODE_URL = "http://localhost:8765"


class TPSBenchmark:
    def __init__(self, node_url):
        self.node_url = node_url
        self.client = PhonesiumClient(node_url)
        self.results = {
            "total_transactions": 0,
            "successful_transactions": 0,
            "failed_transactions": 0,
            "total_time": 0,
            "tps": 0,
            "avg_response_time": 0,
            "min_response_time": 0,
            "max_response_time": 0,
            "response_times": [],
        }

    def print_header(self, title):
        """Print formatted header"""
        print(f"\n{'=' * 70}")
        print(f"{title}")
        print(f"{'=' * 70}\n")

    def create_test_wallets(self, count):
        """Create test wallets for TPS testing"""
        self.print_header(f"CREATING {count} TEST WALLETS")

        wallets = []
        for i in range(count):
            wallet = Wallet()
            wallets.append(
                {
                    "number": i + 1,
                    "address": wallet.address,
                    "private_key": wallet.private_key,
                    "public_key": wallet.public_key,
                    "wallet": wallet,
                }
            )
            if (i + 1) % 10 == 0:
                print(f"Created {i + 1}/{count} wallets...", end="\r")

        print(f"Created {count}/{count} wallets [OK]")
        return wallets

    def get_balance(self, address):
        """Get balance for address"""
        try:
            response = requests.post(
                f"{self.node_url}/get_balance", json={"address": address}, timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                return float(data.get("balance", 0))
            return 0.0
        except Exception as e:
            print(f"Error getting balance: {e}")
            return 0.0

    def fund_wallet(self, sender_wallet, recipient_address, amount):
        """Fund a wallet from sender"""
        try:
            # Create transaction
            tx_data = self.client.create_transaction(
                sender_private_key=sender_wallet.private_key,
                sender_public_key=sender_wallet.public_key,
                recipient_address=recipient_address,
                amount=amount,
                fee=0.02,
            )

            # Submit transaction
            response = requests.post(
                f"{self.node_url}/add_transaction", json=tx_data, timeout=5
            )

            return response.status_code == 200

        except Exception as e:
            return False

    def send_transaction_batch(self, sender_wallet, recipients, amount_per_tx):
        """Send batch of transactions from one wallet"""
        start_time = time.time()
        success_count = 0
        response_times = []

        for recipient in recipients:
            tx_start = time.time()

            try:
                # Create transaction
                tx_data = self.client.create_transaction(
                    sender_private_key=sender_wallet.private_key,
                    sender_public_key=sender_wallet.public_key,
                    recipient_address=recipient["address"],
                    amount=amount_per_tx,
                    fee=0.02,
                )

                # Submit transaction
                response = requests.post(
                    f"{self.node_url}/add_transaction", json=tx_data, timeout=10
                )

                tx_time = time.time() - tx_start
                response_times.append(tx_time)

                if response.status_code == 200:
                    success_count += 1

            except Exception as e:
                pass

        total_time = time.time() - start_time

        return {
            "success_count": success_count,
            "total_count": len(recipients),
            "total_time": total_time,
            "response_times": response_times,
        }

    def parallel_transaction_test(
        self, senders, recipients, amount_per_tx, max_workers=10
    ):
        """Send transactions in parallel from multiple wallets"""
        self.print_header("RUNNING PARALLEL TPS TEST")

        print(f"Senders: {len(senders)}")
        print(f"Recipients per sender: {len(recipients)}")
        print(f"Total transactions: {len(senders) * len(recipients)}")
        print(f"Parallel workers: {max_workers}")
        print(f"\nStarting test...\n")

        start_time = time.time()
        all_response_times = []
        total_success = 0
        total_sent = 0

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all sender tasks
            futures = []
            for sender in senders:
                future = executor.submit(
                    self.send_transaction_batch,
                    sender["wallet"],
                    recipients,
                    amount_per_tx,
                )
                futures.append(future)

            # Collect results
            completed = 0
            for future in as_completed(futures):
                result = future.result()
                total_success += result["success_count"]
                total_sent += result["total_count"]
                all_response_times.extend(result["response_times"])

                completed += 1
                print(
                    f"Progress: {completed}/{len(senders)} senders completed | "
                    f"Success: {total_success}/{total_sent}",
                    end="\r",
                )

        total_time = time.time() - start_time

        print()  # New line after progress

        # Calculate TPS
        tps = total_success / total_time if total_time > 0 else 0

        # Calculate response time statistics
        avg_response = statistics.mean(all_response_times) if all_response_times else 0
        min_response = min(all_response_times) if all_response_times else 0
        max_response = max(all_response_times) if all_response_times else 0

        self.results = {
            "total_transactions": total_sent,
            "successful_transactions": total_success,
            "failed_transactions": total_sent - total_success,
            "total_time": total_time,
            "tps": tps,
            "avg_response_time": avg_response,
            "min_response_time": min_response,
            "max_response_time": max_response,
            "response_times": all_response_times,
        }

        return self.results

    def sequential_transaction_test(self, sender_wallet, recipients, amount_per_tx):
        """Send transactions sequentially (baseline measurement)"""
        self.print_header("RUNNING SEQUENTIAL TPS TEST")

        print(f"Total transactions: {len(recipients)}")
        print(f"\nStarting test...\n")

        result = self.send_transaction_batch(sender_wallet, recipients, amount_per_tx)

        # Calculate TPS
        tps = (
            result["success_count"] / result["total_time"]
            if result["total_time"] > 0
            else 0
        )

        # Calculate response time statistics
        avg_response = (
            statistics.mean(result["response_times"]) if result["response_times"] else 0
        )
        min_response = min(result["response_times"]) if result["response_times"] else 0
        max_response = max(result["response_times"]) if result["response_times"] else 0

        self.results = {
            "total_transactions": result["total_count"],
            "successful_transactions": result["success_count"],
            "failed_transactions": result["total_count"] - result["success_count"],
            "total_time": result["total_time"],
            "tps": tps,
            "avg_response_time": avg_response,
            "min_response_time": min_response,
            "max_response_time": max_response,
            "response_times": result["response_times"],
        }

        return self.results

    def print_results(self):
        """Print benchmark results"""
        self.print_header("TPS BENCHMARK RESULTS")

        print(f"Total Transactions Sent:     {self.results['total_transactions']:,}")
        print(
            f"Successful Transactions:     {self.results['successful_transactions']:,}"
        )
        print(f"Failed Transactions:         {self.results['failed_transactions']:,}")
        print(
            f"Success Rate:                {(self.results['successful_transactions'] / self.results['total_transactions'] * 100):.2f}%"
        )
        print()
        print(f"Total Time:                  {self.results['total_time']:.2f} seconds")
        print(f"Transactions Per Second:     {self.results['tps']:.2f} TPS")
        print()
        print(
            f"Average Response Time:       {self.results['avg_response_time'] * 1000:.2f} ms"
        )
        print(
            f"Min Response Time:           {self.results['min_response_time'] * 1000:.2f} ms"
        )
        print(
            f"Max Response Time:           {self.results['max_response_time'] * 1000:.2f} ms"
        )

        self.print_header("=" * 70)

    def measure_mining_tps(self, duration=60):
        """Measure actual mining TPS (transactions included in blocks)"""
        self.print_header(f"MEASURING MINING TPS ({duration}s)")

        try:
            # Get initial blockchain length
            response = requests.post(f"{self.node_url}/get_blockchain", timeout=5)
            initial_data = response.json()
            initial_chain = initial_data.get("blockchain", [])
            initial_length = len(initial_chain)
            initial_tx_count = sum(
                len(b.get("transactions", [])) for b in initial_chain
            )

            print(f"Initial blockchain length: {initial_length} blocks")
            print(f"Initial transaction count: {initial_tx_count}")
            print(f"\nMonitoring for {duration} seconds...\n")

            start_time = time.time()

            # Monitor for duration
            while time.time() - start_time < duration:
                elapsed = int(time.time() - start_time)
                remaining = duration - elapsed
                print(
                    f"Elapsed: {elapsed}s / {duration}s | Remaining: {remaining}s",
                    end="\r",
                )
                time.sleep(1)

            print()  # New line

            # Get final blockchain length
            response = requests.post(f"{self.node_url}/get_blockchain", timeout=5)
            final_data = response.json()
            final_chain = final_data.get("blockchain", [])
            final_length = len(final_chain)
            final_tx_count = sum(len(b.get("transactions", [])) for b in final_chain)

            # Calculate statistics
            blocks_mined = final_length - initial_length
            transactions_mined = final_tx_count - initial_tx_count
            mining_tps = transactions_mined / duration if duration > 0 else 0
            block_rate = blocks_mined / duration if duration > 0 else 0
            avg_tx_per_block = (
                transactions_mined / blocks_mined if blocks_mined > 0 else 0
            )

            print(f"\n{'=' * 70}")
            print("MINING TPS RESULTS")
            print(f"{'=' * 70}\n")
            print(f"Blocks Mined:                {blocks_mined}")
            print(f"Transactions Mined:          {transactions_mined}")
            print(f"Mining TPS:                  {mining_tps:.2f} TPS")
            print(f"Block Rate:                  {block_rate:.2f} blocks/second")
            print(f"Avg Transactions/Block:      {avg_tx_per_block:.2f}")
            print(f"\n{'=' * 70}\n")

            return {
                "blocks_mined": blocks_mined,
                "transactions_mined": transactions_mined,
                "mining_tps": mining_tps,
                "block_rate": block_rate,
                "avg_tx_per_block": avg_tx_per_block,
            }

        except Exception as e:
            print(f"\n[ERROR] Mining TPS measurement failed: {e}")
            return None


def main():
    """Main TPS testing"""
    print(f"\n{'=' * 70}")
    print("PHN NETWORK - TPS BENCHMARK")
    print(f"{'=' * 70}\n")

    # Check node connection
    print("[*] Connecting to node...")
    try:
        response = requests.get(f"{NODE_URL}/", timeout=5)
        if response.status_code != 200:
            print(f"[[FAIL]] Cannot connect to node at {NODE_URL}")
            print(f"[!] Please start the node first: python -m app.main")
            return False
        print(f"[[OK]] Connected to node at {NODE_URL}\n")
    except Exception as e:
        print(f"[[FAIL]] Cannot connect to node: {e}")
        print(f"[!] Please start the node first: python -m app.main")
        return False

    benchmark = TPSBenchmark(NODE_URL)

    # Load FUND wallet (has tokens to distribute)
    import os
    from dotenv import load_dotenv

    load_dotenv()

    fund_private_key = os.getenv("FUND_PRIVATE_KEY")
    fund_public_key = os.getenv("FUND_PUBLIC_KEY")
    fund_address = os.getenv("FUND_ADDRESS")

    if not all([fund_private_key, fund_public_key, fund_address]):
        print("[[FAIL]] FUND wallet not configured in .env")
        return False

    fund_wallet = Wallet()
    fund_wallet.private_key = fund_private_key
    fund_wallet.public_key = fund_public_key
    fund_wallet.address = fund_address

    # Check FUND balance
    fund_balance = benchmark.get_balance(fund_address)
    print(f"[*] FUND Wallet Balance: {fund_balance:.2f} PHN\n")

    if fund_balance < 100:
        print("[!] WARNING: FUND wallet has low balance. Mine some blocks first.")
        print("[!] Run: python user/cli/miner.py")
        return False

    # Test configuration
    print("=" * 70)
    print("TEST CONFIGURATION")
    print("=" * 70)
    print("\n1. Sequential Test: 100 transactions from 1 wallet")
    print("2. Parallel Test: 500 transactions from 10 wallets (50 each)")
    print("3. Mining TPS: Measure actual block inclusion rate\n")

    # Test 1: Sequential TPS (baseline)
    print("\n[TEST 1] Sequential TPS Test")
    print("-" * 70)

    recipients = benchmark.create_test_wallets(100)
    result1 = benchmark.sequential_transaction_test(fund_wallet, recipients, 0.1)
    benchmark.print_results()

    sequential_tps = result1["tps"]

    # Wait a bit
    print("\n[*] Waiting 5 seconds before next test...\n")
    time.sleep(5)

    # Test 2: Parallel TPS
    print("\n[TEST 2] Parallel TPS Test")
    print("-" * 70)

    # Create sender wallets
    sender_wallets = benchmark.create_test_wallets(10)

    # Fund sender wallets
    print("\n[*] Funding sender wallets...")
    for i, sender in enumerate(sender_wallets):
        success = benchmark.fund_wallet(fund_wallet, sender["address"], 10.0)
        print(f"Funded wallet {i + 1}/10...", end="\r")
        time.sleep(0.1)
    print("Funded wallet 10/10 [OK]   ")

    # Wait for transactions to be included
    print("[*] Waiting 30 seconds for funding transactions to be mined...")
    time.sleep(30)

    # Create recipient wallets
    recipients = benchmark.create_test_wallets(50)

    # Run parallel test
    result2 = benchmark.parallel_transaction_test(
        sender_wallets, recipients, 0.1, max_workers=10
    )
    benchmark.print_results()

    parallel_tps = result2["tps"]

    # Test 3: Mining TPS (optional - requires miner running)
    print("\n[TEST 3] Mining TPS Test")
    print("-" * 70)
    print("\n[!] This test requires a miner to be running.")
    print("[!] Make sure you have started: python user/cli/miner.py\n")

    response = input("Press Enter to start mining TPS test (or Ctrl+C to skip): ")

    mining_result = benchmark.measure_mining_tps(duration=60)

    # Final Summary
    print("\n" + "=" * 70)
    print("FINAL TPS SUMMARY")
    print("=" * 70)
    print(f"\nSequential TPS:              {sequential_tps:.2f} TPS")
    print(f"Parallel TPS:                {parallel_tps:.2f} TPS")

    if mining_result:
        print(f"Mining TPS (actual):         {mining_result['mining_tps']:.2f} TPS")
        print(f"\nNote: Mining TPS is limited by block time and difficulty.")
        print(f"      To increase mining TPS, reduce difficulty or increase miners.")

    print("\n" + "=" * 70)
    print("PHN Network can handle:")
    print(f"  - Submission Rate: {parallel_tps:.2f} TPS")
    print(
        f"  - Processing Rate: {mining_result['mining_tps']:.2f} TPS"
        if mining_result
        else "  - Processing Rate: N/A (no miner running)"
    )
    print("=" * 70 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[!] Benchmark interrupted by user")
        sys.exit(0)
