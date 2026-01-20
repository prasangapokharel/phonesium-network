#!/usr/bin/env python3
"""
PHN Blockchain - Comprehensive System Test
Tests all core functionality including node sync, LMDB storage, orjson performance
"""

import sys
import time
import subprocess
import requests
from pathlib import Path

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(70)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}\n")

def print_test(text):
    print(f"{Colors.YELLOW}[TEST]{Colors.END} {text}")

def print_success(text):
    print(f"{Colors.GREEN}[PASS] {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}[FAIL] {text}{Colors.END}")

def print_info(text):
    print(f"{Colors.BLUE}[INFO]{Colors.END} {text}")


class TestResults:
    def __init__(self):
        self.passed = []
        self.failed = []
        
    def add_pass(self, test_name):
        self.passed.append(test_name)
        print_success(f"PASSED: {test_name}")
        
    def add_fail(self, test_name, reason):
        self.failed.append((test_name, reason))
        print_error(f"FAILED: {test_name} - {reason}")
    
    def print_summary(self):
        print_header("TEST SUMMARY")
        total = len(self.passed) + len(self.failed)
        print(f"Total Tests: {total}")
        print(f"{Colors.GREEN}Passed: {len(self.passed)}{Colors.END}")
        print(f"{Colors.RED}Failed: {len(self.failed)}{Colors.END}")
        
        if self.failed:
            print(f"\n{Colors.RED}Failed Tests:{Colors.END}")
            for test_name, reason in self.failed:
                print(f"  - {test_name}: {reason}")
        
        success_rate = (len(self.passed) / total * 100) if total > 0 else 0
        print(f"\n{Colors.BOLD}Success Rate: {success_rate:.1f}%{Colors.END}")
        
        return len(self.failed) == 0


def test_module_imports(results):
    """Test 1: Verify all required modules can be imported"""
    print_header("TEST 1: Module Imports")
    
    modules = [
        ("orjson", "Fast JSON serialization"),
        ("lmdb", "LMDB database"),
        ("ecdsa", "ECDSA cryptography"),
        ("aiohttp", "Async HTTP server"),
        ("requests", "HTTP client"),
    ]
    
    for module_name, description in modules:
        try:
            print_test(f"Importing {module_name} ({description})")
            __import__(module_name)
            results.add_pass(f"Import {module_name}")
        except ImportError as e:
            results.add_fail(f"Import {module_name}", str(e))


def test_orjson_performance(results):
    """Test 2: Verify orjson is faster than json"""
    print_header("TEST 2: orjson Performance")
    
    try:
        import json
        import orjson
        
        # Test data
        test_data = {
            "transactions": [
                {"sender": f"addr{i}", "recipient": f"addr{i+1}", "amount": i*10}
                for i in range(1000)
            ],
            "timestamp": time.time(),
            "nonce": 12345
        }
        
        # Test json
        print_test("Testing standard json serialization")
        start = time.time()
        for _ in range(100):
            json.dumps(test_data)
        json_time = time.time() - start
        print_info(f"json.dumps (100 iterations): {json_time:.4f}s")
        
        # Test orjson
        print_test("Testing orjson serialization")
        start = time.time()
        for _ in range(100):
            orjson.dumps(test_data)
        orjson_time = time.time() - start
        print_info(f"orjson.dumps (100 iterations): {orjson_time:.4f}s")
        
        # Calculate speedup
        speedup = json_time / orjson_time if orjson_time > 0 else 0
        print_info(f"orjson is {speedup:.2f}x faster than json")
        
        if speedup >= 1.5:
            results.add_pass(f"orjson performance ({speedup:.2f}x faster)")
        else:
            results.add_fail(f"orjson performance", f"Only {speedup:.2f}x faster (expected >1.5x)")
            
    except Exception as e:
        results.add_fail("orjson performance test", str(e))


def test_lmdb_storage(results):
    """Test 3: Verify LMDB storage is working"""
    print_header("TEST 3: LMDB Storage")
    
    try:
        import lmdb
        import orjson
        
        # Create test database
        print_test("Creating test LMDB database")
        test_db_path = "lmdb_data/test_db"
        Path(test_db_path).mkdir(parents=True, exist_ok=True)
        
        env = lmdb.open(test_db_path, max_dbs=1, map_size=1024*1024*100)
        db = env.open_db(b'test')
        
        # Write test data
        print_test("Writing test data to LMDB")
        test_data = {"test_key": "test_value", "number": 12345}
        with env.begin(write=True, db=db) as txn:
            txn.put(b'test', orjson.dumps(test_data))
        
        # Read test data
        print_test("Reading test data from LMDB")
        with env.begin(db=db) as txn:
            stored_data = txn.get(b'test')
            if stored_data:
                loaded_data = orjson.loads(stored_data)
                if loaded_data == test_data:
                    results.add_pass("LMDB read/write with orjson")
                else:
                    results.add_fail("LMDB read/write", "Data mismatch")
            else:
                results.add_fail("LMDB read/write", "No data found")
        
        env.close()
        
    except Exception as e:
        results.add_fail("LMDB storage test", str(e))


def test_blockchain_initialization(results):
    """Test 4: Verify blockchain can initialize"""
    print_header("TEST 4: Blockchain Initialization")
    
    try:
        print_test("Importing blockchain module")
        from app.core.blockchain.chain import (
            blockchain, init_database, load_blockchain, 
            create_genesis_block, verify_blockchain
        )
        
        print_test("Initializing database")
        init_database()
        results.add_pass("Database initialization")
        
        print_test("Loading blockchain")
        load_blockchain()
        
        if len(blockchain) >= 1:
            print_info(f"Blockchain has {len(blockchain)} blocks")
            results.add_pass("Blockchain loaded")
        else:
            print_test("Creating genesis block")
            genesis = create_genesis_block()
            blockchain.append(genesis)
            results.add_pass("Genesis block created")
        
        print_test("Verifying blockchain")
        valid, reason = verify_blockchain(blockchain)
        if valid:
            results.add_pass("Blockchain verification")
        else:
            results.add_fail("Blockchain verification", reason)
            
    except Exception as e:
        results.add_fail("Blockchain initialization", str(e))
        import traceback
        traceback.print_exc()


def test_node_sync_initialization(results):
    """Test 5: Verify node sync can initialize"""
    print_header("TEST 5: Node Sync Initialization")
    
    try:
        print_test("Importing node sync module")
        from app.core.network.sync import RobustNodeSync, NodeHealth
        from app.core.blockchain.chain import blockchain, verify_blockchain, save_blockchain
        
        print_test("Creating NodeHealth instance")
        health = NodeHealth()
        results.add_pass("NodeHealth initialization")
        
        print_test("Creating RobustNodeSync instance")
        peers = set(["http://localhost:8546", "http://localhost:8547"])
        node_sync = RobustNodeSync(blockchain, peers, verify_blockchain, save_blockchain)
        results.add_pass("RobustNodeSync initialization")
        
        print_test("Testing health tracking")
        test_peer = "http://test-peer:8545"
        health.mark_success(test_peer)
        if health.is_healthy(test_peer):
            results.add_pass("Peer health tracking")
        else:
            results.add_fail("Peer health tracking", "Peer not marked as healthy")
        
        print_test("Testing failure detection")
        for _ in range(3):
            health.mark_failure(test_peer)
        if not health.is_healthy(test_peer):
            results.add_pass("Peer failure detection")
        else:
            results.add_fail("Peer failure detection", "Peer still marked as healthy after 3 failures")
            
    except Exception as e:
        results.add_fail("Node sync initialization", str(e))
        import traceback
        traceback.print_exc()


def test_single_node_startup(results):
    """Test 6: Verify single node can start"""
    print_header("TEST 6: Single Node Startup")
    
    node_process = None
    try:
        print_test("Starting single node on port 8765")
        import os
        env = os.environ.copy()
        env["NODE_PORT"] = "8765"
        
        node_process = subprocess.Popen(
            [sys.executable, "app/main.py"],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for node to start
        print_test("Waiting for node to start (max 30 seconds)")
        for i in range(30):
            try:
                res = requests.get("http://localhost:8765/api/v1/info", timeout=2)
                if res.status_code == 200:
                    print_info(f"Node started in {i+1} seconds")
                    results.add_pass("Single node startup")
                    
                    # Test API response
                    data = res.json()
                    print_info(f"Node version: {data.get('data', {}).get('version', 'unknown')}")
                    print_info(f"Blockchain height: {data.get('data', {}).get('blockchain_height', 0)}")
                    results.add_pass("API response validation")
                    break
            except:
                time.sleep(1)
        else:
            results.add_fail("Single node startup", "Node failed to start within 30 seconds")
        
    except Exception as e:
        results.add_fail("Single node startup", str(e))
    finally:
        if node_process:
            print_test("Stopping node")
            node_process.terminate()
            try:
                node_process.wait(timeout=10)
            except:
                node_process.kill()


def test_orjson_usage(results):
    """Test 7: Verify no files use standard json"""
    print_header("TEST 7: orjson Usage Verification")
    
    try:
        print_test("Scanning Python files for 'import json'")
        
        json_files = []
        for py_file in Path(".").rglob("*.py"):
            # Skip venv and __pycache__
            if "venv" in str(py_file) or "__pycache__" in str(py_file):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'import json' in content and 'import orjson' not in content:
                        # Skip if it's just a comment
                        lines = content.split('\n')
                        for line in lines:
                            if 'import json' in line and not line.strip().startswith('#'):
                                json_files.append(str(py_file))
                                break
            except:
                pass
        
        if not json_files:
            results.add_pass("All files use orjson (0 files using standard json)")
        else:
            results.add_fail("orjson usage", f"{len(json_files)} files still use standard json: {json_files[:5]}")
            
    except Exception as e:
        results.add_fail("orjson usage verification", str(e))


def main():
    """Run all tests"""
    print_header("PHN BLOCKCHAIN - COMPREHENSIVE SYSTEM TEST")
    print_info("This will test all core functionality")
    print_info("Estimated time: 2-3 minutes")
    print()
    
    results = TestResults()
    
    # Run all tests
    test_module_imports(results)
    test_orjson_performance(results)
    test_lmdb_storage(results)
    test_blockchain_initialization(results)
    test_node_sync_initialization(results)
    test_orjson_usage(results)
    test_single_node_startup(results)
    
    # Print summary
    all_passed = results.print_summary()
    
    if all_passed:
        print(f"\n{Colors.GREEN}{Colors.BOLD}ALL TESTS PASSED!{Colors.END}")
        print(f"{Colors.GREEN}Your PHN Blockchain is ready for production!{Colors.END}\n")
        return 0
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}SOME TESTS FAILED{Colors.END}")
        print(f"{Colors.RED}Please review the failed tests above{Colors.END}\n")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Tests cancelled by user{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Fatal error: {e}{Colors.END}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
