"""
Test script for balance cache performance
Compares cached vs full calculation
"""

import time
import sys
import os

# Add the project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.blockchain.chain import (
    load_blockchain,
    init_database,
    get_balance,
    _calculate_balance_full,
    balance_cache,
    rebuild_balance_cache,
)


def test_balance_cache():
    """Test balance cache performance and accuracy"""
    print("=" * 60)
    print("BALANCE CACHE PERFORMANCE TEST")
    print("=" * 60)

    # Initialize and load blockchain
    print("\n[1] Initializing database and loading blockchain...")
    init_database()
    load_blockchain()

    from app.core.blockchain.chain import blockchain

    print(f"[OK] Loaded {len(blockchain)} blocks")

    if len(blockchain) == 0:
        print("! No blocks in blockchain, cannot test")
        return

    # Rebuild cache to ensure it's fresh
    print("\n[2] Rebuilding balance cache...")
    rebuild_balance_cache()
    print(f"[OK] Cache contains {len(balance_cache)} addresses")

    if len(balance_cache) == 0:
        print("! No addresses in cache, blockchain may not have transactions")
        return

    # Get test addresses from cache
    test_addresses = list(balance_cache.keys())[:5]  # Test first 5 addresses
    print(f"\n[3] Testing {len(test_addresses)} addresses...")

    results = []

    for i, address in enumerate(test_addresses, 1):
        print(f"\n--- Test {i}/{len(test_addresses)}: {address[:20]}... ---")

        # Test 1: Cached balance (FAST)
        start = time.perf_counter()
        cached_balance = get_balance(address)
        cached_time = time.perf_counter() - start

        # Test 2: Full calculation (SLOW)
        # Temporarily clear cache for this address
        cache_backup = balance_cache.pop(address, None)

        start = time.perf_counter()
        full_balance = _calculate_balance_full(address)
        full_time = time.perf_counter() - start

        # Restore cache
        if cache_backup:
            balance_cache[address] = cache_backup

        # Compare results
        balance_match = abs(cached_balance - full_balance) < 1e-6
        speedup = full_time / cached_time if cached_time > 0 else float("inf")

        results.append(
            {
                "address": address[:20] + "...",
                "cached_balance": cached_balance,
                "full_balance": full_balance,
                "cached_time_ms": cached_time * 1000,
                "full_time_ms": full_time * 1000,
                "speedup": speedup,
                "match": balance_match,
            }
        )

        # Print results
        status = "[OK]" if balance_match else "[ERROR]"
        print(
            f"{status} Cached balance: {cached_balance:.6f} PHN ({cached_time * 1000:.2f}ms)"
        )
        print(
            f"{status} Full balance:   {full_balance:.6f} PHN ({full_time * 1000:.2f}ms)"
        )
        print(f"  Speedup: {speedup:.1f}x faster")
        print(f"  Match: {'YES' if balance_match else 'NO - ERROR!'}")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    all_match = all(r["match"] for r in results)
    avg_speedup = sum(r["speedup"] for r in results) / len(results)
    avg_cached_time = sum(r["cached_time_ms"] for r in results) / len(results)
    avg_full_time = sum(r["full_time_ms"] for r in results) / len(results)

    print(f"\nTested: {len(results)} addresses")
    print(f"Accuracy: {'[OK] ALL CORRECT' if all_match else '[ERROR] SOME ERRORS'}")
    print(f"\nPerformance:")
    print(f"  Average cached time: {avg_cached_time:.2f}ms")
    print(f"  Average full time:   {avg_full_time:.2f}ms")
    print(f"  Average speedup:     {avg_speedup:.1f}x faster")

    print("\n" + "=" * 60)

    if all_match and avg_speedup > 5:
        print("[OK] SUCCESS: Balance cache is working correctly and fast!")
    elif all_match:
        print("[!] WARNING: Cache is accurate but speedup is low")
    else:
        print("[ERROR] FAILURE: Cache has accuracy errors!")

    print("=" * 60)

    return all_match and avg_speedup > 1


if __name__ == "__main__":
    try:
        success = test_balance_cache()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] ERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
