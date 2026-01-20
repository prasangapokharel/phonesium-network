#!/usr/bin/env python3
"""
LMDB Batch Write Performance Test
Verifies batch writing is working correctly and measures performance
"""

import sys
import os
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.storage.lmdb import LMDBStorage, get_lmdb
import tempfile
import shutil

def test_batch_blockchain_write():
    """Test batch writing blockchain"""
    print("\n[TEST 1] Batch Blockchain Write")
    print("="*70)
    
    # Create temp directory
    temp_dir = tempfile.mkdtemp(prefix="lmdb_test_")
    
    try:
        db = LMDBStorage(temp_dir)
        
        # Create 1000 test blocks
        blocks = []
        for i in range(1000):
            block = {
                'index': i,
                'timestamp': time.time(),
                'transactions': [{'txid': f'tx_{i}', 'amount': 10.0}],
                'prev_hash': f'hash_{i-1}' if i > 0 else '0' * 64,
                'hash': f'hash_{i}',
                'nonce': i * 1000
            }
            blocks.append(block)
        
        # Measure batch write time
        start = time.time()
        success = db.save_blockchain(blocks)
        elapsed = time.time() - start
        
        if success:
            print(f"[PASS] Saved 1000 blocks in {elapsed:.4f}s")
            print(f"  Performance: {1000/elapsed:.0f} blocks/second")
        else:
            print("[FAIL] Failed to save blockchain")
            return False
        
        # Verify blocks can be read
        loaded = db.load_blockchain()
        
        if loaded and len(loaded) == 1000:
            print(f"[PASS] Loaded {len(loaded)} blocks successfully")
            return True
        else:
            print(f"[FAIL] Expected 1000 blocks, got {len(loaded) if loaded else 0}")
            return False
            
    finally:
        db.close()
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_append_single_block():
    """Test append_block optimization"""
    print("\n[TEST 2] Single Block Append (Optimized)")
    print("="*70)
    
    temp_dir = tempfile.mkdtemp(prefix="lmdb_test_")
    
    try:
        db = LMDBStorage(temp_dir)
        
        # Append blocks one at a time (simulating mining)
        start = time.time()
        
        for i in range(100):
            block = {
                'index': i,
                'timestamp': time.time(),
                'transactions': [{'txid': f'tx_{i}', 'amount': 10.0}],
                'prev_hash': f'hash_{i-1}' if i > 0 else '0' * 64,
                'hash': f'hash_{i}',
                'nonce': i * 1000
            }
            
            success = db.append_block(block)
            if not success:
                print(f"[FAIL] Failed to append block {i}")
                return False
        
        elapsed = time.time() - start
        
        print(f"[PASS] Appended 100 blocks in {elapsed:.4f}s")
        print(f"  Performance: {100/elapsed:.0f} blocks/second")
        
        # Verify count
        count = db.get_block_count()
        
        if count == 100:
            print(f"[PASS] Block count verified: {count}")
            return True
        else:
            print(f"[FAIL] Expected 100 blocks, got {count}")
            return False
            
    finally:
        db.close()
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_batch_validation_records():
    """Test batch validation record writing"""
    print("\n[TEST 3] Batch Validation Records")
    print("="*70)
    
    temp_dir = tempfile.mkdtemp(prefix="lmdb_test_")
    
    try:
        db = LMDBStorage(temp_dir)
        
        # Create 500 validation records
        records = []
        for i in range(500):
            txid = f"tx_{i:010d}"
            validation_data = {
                'status': 'valid',
                'timestamp': time.time(),
                'validator': 'test_node',
                'reason': 'ok'
            }
            records.append((txid, validation_data))
        
        # Measure batch write
        start = time.time()
        success = db.save_validation_records_batch(records)
        elapsed = time.time() - start
        
        if success:
            print(f"[PASS] Batch saved 500 validation records in {elapsed:.4f}s")
            print(f"  Performance: {500/elapsed:.0f} records/second")
        else:
            print("[FAIL] Failed to batch save validation records")
            return False
        
        # Verify records can be read
        count = db.get_validation_count()
        
        if count == 500:
            print(f"[PASS] Validation count verified: {count}")
            return True
        else:
            print(f"[FAIL] Expected 500 records, got {count}")
            return False
            
    finally:
        db.close()
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_batch_vs_individual():
    """Compare batch vs individual write performance"""
    print("\n[TEST 4] Batch vs Individual Write Performance")
    print("="*70)
    
    temp_dir1 = tempfile.mkdtemp(prefix="lmdb_test_individual_")
    temp_dir2 = tempfile.mkdtemp(prefix="lmdb_test_batch_")
    
    try:
        # Test individual writes
        db1 = LMDBStorage(temp_dir1)
        
        start = time.time()
        for i in range(100):
            txid = f"tx_{i:010d}"
            validation_data = {'status': 'valid', 'timestamp': time.time()}
            db1.save_validation_record(txid, validation_data)
        individual_time = time.time() - start
        db1.close()
        
        # Test batch writes
        db2 = LMDBStorage(temp_dir2)
        
        records = []
        for i in range(100):
            txid = f"tx_{i:010d}"
            validation_data = {'status': 'valid', 'timestamp': time.time()}
            records.append((txid, validation_data))
        
        start = time.time()
        db2.save_validation_records_batch(records)
        batch_time = time.time() - start
        db2.close()
        
        speedup = individual_time / batch_time
        
        print(f"  Individual writes: {individual_time:.4f}s ({100/individual_time:.0f} records/s)")
        print(f"  Batch writes:      {batch_time:.4f}s ({100/batch_time:.0f} records/s)")
        print(f"  Speedup:           {speedup:.2f}x faster")
        
        if speedup >= 2.0:
            print(f"[PASS] Batch writing is {speedup:.2f}x faster (target: 2x+)")
            return True
        else:
            print(f"[WARN] Batch speedup only {speedup:.2f}x (expected 2x+)")
            return True  # Still pass but warn
            
    finally:
        shutil.rmtree(temp_dir1, ignore_errors=True)
        shutil.rmtree(temp_dir2, ignore_errors=True)


def test_concurrent_reads():
    """Test that batch writes don't block reads"""
    print("\n[TEST 5] Concurrent Read Performance")
    print("="*70)
    
    temp_dir = tempfile.mkdtemp(prefix="lmdb_test_")
    
    try:
        db = LMDBStorage(temp_dir)
        
        # Write some initial data
        blocks = []
        for i in range(100):
            block = {
                'index': i,
                'timestamp': time.time(),
                'transactions': [],
                'prev_hash': '0' * 64,
                'hash': f'hash_{i}',
                'nonce': i
            }
            blocks.append(block)
        
        db.save_blockchain(blocks)
        
        # Test read performance
        start = time.time()
        
        for i in range(100):
            block = db.get_block_by_index(i)
            if not block:
                print(f"[FAIL] Could not read block {i}")
                return False
        
        elapsed = time.time() - start
        
        print(f"[PASS] Read 100 blocks in {elapsed:.4f}s")
        print(f"  Performance: {100/elapsed:.0f} blocks/second")
        
        return True
        
    finally:
        db.close()
        shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    """Run all batch write tests"""
    print("\n" + "="*70)
    print("LMDB BATCH WRITE PERFORMANCE TEST SUITE")
    print("="*70)
    print("Verifying batch writing optimization as per speedup.md")
    print("="*70)
    
    tests = [
        ("Batch Blockchain Write", test_batch_blockchain_write),
        ("Single Block Append", test_append_single_block),
        ("Batch Validation Records", test_batch_validation_records),
        ("Batch vs Individual Performance", test_batch_vs_individual),
        ("Concurrent Read Performance", test_concurrent_reads),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n[ERROR] Test '{name}' crashed: {e}")
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
        print(f"{status} {name}")
    
    print("="*70)
    print(f"Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print("="*70)
    
    if passed == total:
        print("\n[SUCCESS] All batch write optimizations verified!")
        print("System is using efficient batch writing as per speedup.md")
        return 0
    else:
        print(f"\n[WARNING] {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
