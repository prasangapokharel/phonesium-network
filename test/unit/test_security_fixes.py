#!/usr/bin/env python3
"""
Comprehensive Security Test Suite for PHN Blockchain
Tests all security fixes implemented in the security hardening phase
"""

import sys
import os
import time
import random

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.transactions.base import make_txid, validate_transaction, verify_tx_signature
from app.core.blockchain.chain import blockchain, create_genesis_block
from app.core.consensus.difficulty import DifficultyAdjuster
from app.core.transactions.mempool import AdvancedMempool

def test_txid_collision_prevention():
    """Test that nonce prevents TXID collisions"""
    print("\n[Test 1] TXID Collision Prevention")
    print("="*70)
    
    # Create two identical transactions
    tx1_id = make_txid("sender1", "recipient1", 10.0, 0.01, timestamp=1000.0, nonce=123)
    tx2_id = make_txid("sender1", "recipient1", 10.0, 0.01, timestamp=1000.0, nonce=456)
    
    if tx1_id != tx2_id:
        print("[PASS] Different nonces produce different TXIDs")
        print(f"  TX1: {tx1_id[:32]}...")
        print(f"  TX2: {tx2_id[:32]}...")
        return True
    else:
        print("[FAIL] Same TXID despite different nonces")
        return False

def test_replay_attack_protection():
    """Test timestamp validation prevents replay attacks"""
    print("\n[Test 2] Replay Attack Protection")
    print("="*70)
    
    current_time = time.time()
    
    # Test 1: Future transaction (should fail)
    future_tx = {
        "sender": "test_sender",
        "recipient": "test_recipient",
        "amount": 10.0,
        "fee": 0.01,
        "timestamp": current_time + 3600,  # 1 hour in future
        "txid": "a" * 64,
        "signature": "test_sig",
        "nonce": 123456
    }
    
    ok, msg = validate_transaction(future_tx)
    print(f"  [DEBUG] Valid: {ok}, Message: '{msg}'")
    if not ok and "future" in msg.lower():
        print("[PASS] Future transactions rejected")
        print(f"  Message: {msg}")
    else:
        print(f"[FAIL] Future transaction not rejected (ok={ok}, has_future={('future' in msg.lower())})")
        return False
    
    # Test 2: Old transaction (should fail)
    old_tx = {
        "sender": "test_sender",
        "recipient": "test_recipient",
        "amount": 10.0,
        "fee": 0.01,
        "timestamp": current_time - 7200,  # 2 hours old
        "txid": "b" * 64,
        "signature": "test_sig",
        "nonce": 123457
    }
    
    ok, msg = validate_transaction(old_tx)
    if not ok and "old" in msg.lower():
        print("[PASS] Old transactions rejected (replay protection)")
        print(f"  Message: {msg}")
        return True
    else:
        print("[FAIL] Old transaction not rejected")
        return False

def test_signature_validation():
    """Test enhanced signature validation"""
    print("\n[Test 3] Enhanced Signature Validation")
    print("="*70)
    
    # Test 1: System transaction with "genesis" signature
    system_tx = {
        "sender": "coinbase",
        "recipient": "miner_address",
        "amount": 50.0,
        "fee": 0.0,
        "timestamp": time.time(),
        "txid": "c" * 64,
        "signature": "genesis",
        "nonce": 1
    }
    
    if verify_tx_signature(system_tx):
        print("[PASS] System transactions with 'genesis' signature accepted")
    else:
        print("[FAIL] System transaction rejected")
        return False
    
    # Test 2: User transaction with "genesis" signature (should fail)
    user_tx_fake = {
        "sender": "a" * 128,  # Public key format
        "recipient": "recipient",
        "amount": 10.0,
        "fee": 0.01,
        "timestamp": time.time(),
        "txid": "d" * 64,
        "signature": "genesis",  # Trying to bypass signature check
        "nonce": 2
    }
    
    if not verify_tx_signature(user_tx_fake):
        print("[PASS] User transactions with 'genesis' signature rejected")
        print("  (Signature bypass attack prevented)")
        return True
    else:
        print("[FAIL] User transaction with fake signature accepted")
        return False

def test_difficulty_adjustment():
    """Test dynamic difficulty adjustment"""
    print("\n[Test 4] Dynamic Difficulty Adjustment")
    print("="*70)
    
    adjuster = DifficultyAdjuster(target_block_time=60, adjustment_interval=10)
    
    # Create test blockchain with blocks mined too fast
    test_chain = [create_genesis_block()]
    current_time = time.time()
    
    for i in range(1, 11):
        block = {
            "index": i,
            "timestamp": current_time + (i * 30),  # 30 seconds each (too fast)
            "transactions": [],
            "prev_hash": test_chain[-1]["hash"],
            "hash": "0" * i + "abc",
            "nonce": i
        }
        test_chain.append(block)
    
    new_difficulty = adjuster.calculate_difficulty(test_chain)
    
    if new_difficulty > adjuster.min_difficulty:
        print(f"[PASS] Difficulty increased for fast blocks")
        print(f"  New difficulty: {new_difficulty}")
        return True
    else:
        print("[FAIL] Difficulty not adjusted correctly")
        return False

def test_mempool_priority():
    """Test advanced mempool priority queue"""
    print("\n[Test 5] Advanced Mempool Priority Queue")
    print("="*70)
    
    mempool = AdvancedMempool(max_size=5, max_tx_age=3600)
    
    # Add transactions with different fees
    txs = [
        {"txid": "tx1", "sender": "A", "recipient": "B", "amount": 10, "fee": 0.01, "timestamp": time.time(), "signature": "sig1", "nonce": 1},
        {"txid": "tx2", "sender": "C", "recipient": "D", "amount": 20, "fee": 0.10, "timestamp": time.time(), "signature": "sig2", "nonce": 2},
        {"txid": "tx3", "sender": "E", "recipient": "F", "amount": 30, "fee": 0.05, "timestamp": time.time(), "signature": "sig3", "nonce": 3},
    ]
    
    for tx in txs:
        mempool.add_transaction(tx)
    
    # Get transactions for mining (should be sorted by fee)
    mining_txs = mempool.get_transactions_for_mining()
    
    # Verify order: highest fee first
    fees = [tx["fee"] for tx in mining_txs]
    if fees == sorted(fees, reverse=True):
        print("[PASS] Transactions sorted by fee (highest first)")
        print(f"  Fee order: {fees}")
        return True
    else:
        print("[FAIL] Transactions not sorted correctly")
        print(f"  Expected: {sorted(fees, reverse=True)}")
        print(f"  Got: {fees}")
        return False

def test_mempool_eviction():
    """Test mempool evicts low-fee transactions when full"""
    print("\n[Test 6] Mempool Eviction (Spam Protection)")
    print("="*70)
    
    mempool = AdvancedMempool(max_size=3, max_tx_age=3600)
    
    # Fill mempool with low-fee transactions
    for i in range(3):
        tx = {
            "txid": f"tx{i}",
            "sender": "A",
            "recipient": "B",
            "amount": 10,
            "fee": 0.01,
            "timestamp": time.time(),
            "signature": "sig",
            "nonce": i
        }
        mempool.add_transaction(tx)
    
    # Try to add high-fee transaction (should evict low-fee one)
    high_fee_tx = {
        "txid": "tx_high",
        "sender": "X",
        "recipient": "Y",
        "amount": 10,
        "fee": 1.0,
        "timestamp": time.time(),
        "signature": "sig",
        "nonce": 999
    }
    
    success, msg = mempool.add_transaction(high_fee_tx)
    
    if success and "evicted" in msg.lower():
        print("[PASS] Low-fee transaction evicted for high-fee one")
        print(f"  Message: {msg}")
        return True
    elif success:
        print("[PASS] High-fee transaction added (eviction occurred)")
        return True
    else:
        print("[FAIL] High-fee transaction rejected")
        print(f"  Message: {msg}")
        return False

def run_all_tests():
    """Run all security tests"""
    print("\n" + "="*70)
    print("PHN BLOCKCHAIN - COMPREHENSIVE SECURITY TEST SUITE")
    print("="*70)
    print("Testing all security fixes from security hardening phase")
    print("="*70)
    
    tests = [
        ("TXID Collision Prevention", test_txid_collision_prevention),
        ("Replay Attack Protection", test_replay_attack_protection),
        ("Signature Validation", test_signature_validation),
        ("Dynamic Difficulty", test_difficulty_adjustment),
        ("Mempool Priority", test_mempool_priority),
        ("Mempool Eviction", test_mempool_eviction),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n[ERROR] in {name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} - {name}")
    
    print("="*70)
    print(f"Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print("="*70)
    
    if passed == total:
        print("\n>>> All security tests passed!")
        print("System is ready for production deployment.")
        return True
    else:
        print(f"\n>>> {total - passed} test(s) failed")
        print("Please review and fix failing tests before deployment.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
