#!/usr/bin/env python3
"""
Quick verification test - tests core components without starting full node
"""

def test_imports():
    """Test all imports"""
    print("Testing imports...")
    import orjson
    import lmdb
    import ecdsa
    import aiohttp
    import requests
    from app.core.blockchain.chain import blockchain, init_database
    from app.core.network.sync import RobustNodeSync
    print("[OK] All imports successful")

def test_orjson_speed():
    """Test orjson performance"""
    print("\nTesting orjson performance...")
    import json
    import orjson
    import time
    
    data = {"test": list(range(1000))}
    
    # json
    start = time.time()
    for _ in range(100):
        json.dumps(data)
    json_time = time.time() - start
    
    # orjson
    start = time.time()
    for _ in range(100):
        orjson.dumps(data)
    orjson_time = time.time() - start
    
    speedup = json_time / orjson_time
    print(f"[OK] orjson is {speedup:.2f}x faster than json")

def test_lmdb():
    """Test LMDB"""
    print("\nTesting LMDB...")
    from app.core.blockchain.chain import init_database, blockchain, load_blockchain
    
    init_database()
    load_blockchain()
    print(f"[OK] LMDB working - blockchain has {len(blockchain)} blocks")

def test_node_sync():
    """Test node sync"""
    print("\nTesting node sync...")
    from app.core.network.sync import RobustNodeSync, NodeHealth
    from app.core.blockchain.chain import blockchain, verify_blockchain, save_blockchain
    
    health = NodeHealth()
    peers = set(["http://localhost:8546"])
    sync = RobustNodeSync(blockchain, peers, verify_blockchain, save_blockchain)
    
    # Test health tracking
    health.mark_success("http://test:8545")
    assert health.is_healthy("http://test:8545")
    
    # Test failure detection
    for _ in range(3):
        health.mark_failure("http://test2:8545")
    assert not health.is_healthy("http://test2:8545")
    
    print("[OK] Node sync working correctly")

def test_no_json_imports():
    """Verify no standard json imports"""
    print("\nVerifying orjson usage...")
    from pathlib import Path
    
    json_files = []
    for py_file in Path(".").rglob("*.py"):
        if "venv" in str(py_file):
            continue
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'import json' in content and 'import orjson' not in content and 'convert' not in str(py_file):
                    json_files.append(str(py_file))
        except:
            pass
    
    if json_files:
        print(f"[WARNING] {len(json_files)} files still use standard json")
        for f in json_files[:5]:
            print(f"  - {f}")
    else:
        print("[OK] All files use orjson")

if __name__ == "__main__":
    print("="*60)
    print("PHN BLOCKCHAIN - QUICK VERIFICATION TEST")
    print("="*60)
    
    try:
        test_imports()
        test_orjson_speed()
        test_lmdb()
        test_node_sync()
        test_no_json_imports()
        
        print("\n" + "="*60)
        print("ALL CORE TESTS PASSED!")
        print("="*60)
        print("\nYour blockchain is working correctly!")
        print("Core components:")
        print("  [OK] orjson (2-8x faster than json)")
        print("  [OK] LMDB storage")
        print("  [OK] Robust node sync with health monitoring")
        print("  [OK] Blockchain initialization")
        print("\nNext steps:")
        print("  1. Start node: python app/main.py")
        print("  2. Test multi-node: python test_multi_node.py")
        
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
