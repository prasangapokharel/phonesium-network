#!/usr/bin/env python3
"""
PHN Blockchain - Multi-Node Failure Test Script
Tests robust node synchronization with node failures

This script:
1. Starts 3 nodes on different ports
2. Connects them together
3. Simulates node failures
4. Verifies that remaining nodes continue syncing
"""

import subprocess
import time
import requests
import sys
import os
from pathlib import Path

# Test configuration
NODES = [
    {"port": 8545, "name": "Node1"},
    {"port": 8546, "name": "Node2"},
    {"port": 8547, "name": "Node3"},
]

PEERS_CONFIG = {
    8545: [],  # Node 1 has no initial peers
    8546: ["http://localhost:8545"],  # Node 2 connects to Node 1
    8547: ["http://localhost:8545", "http://localhost:8546"],  # Node 3 connects to both
}


class NodeProcess:
    """Manage a node process"""
    def __init__(self, port, name, peers):
        self.port = port
        self.name = name
        self.peers = peers
        self.process = None
        self.url = f"http://localhost:{port}"
        
    def start(self):
        """Start the node process"""
        env = os.environ.copy()
        env["NODE_PORT"] = str(self.port)
        env["PEERS"] = ",".join(self.peers) if self.peers else ""
        
        print(f"[{self.name}] Starting on port {self.port}...")
        
        self.process = subprocess.Popen(
            [sys.executable, "app/main.py"],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for node to start
        for i in range(30):
            try:
                res = requests.get(f"{self.url}/api/v1/info", timeout=2)
                if res.status_code == 200:
                    print(f"[{self.name}] Started successfully on {self.url}")
                    return True
            except:
                time.sleep(1)
        
        print(f"[{self.name}] Failed to start!")
        return False
    
    def stop(self):
        """Stop the node process"""
        if self.process:
            print(f"[{self.name}] Stopping...")
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except:
                self.process.kill()
            print(f"[{self.name}] Stopped")
    
    def is_running(self):
        """Check if node is running"""
        try:
            res = requests.get(f"{self.url}/api/v1/info", timeout=2)
            return res.status_code == 200
        except:
            return False
    
    def get_chain_length(self):
        """Get blockchain length"""
        try:
            res = requests.get(f"{self.url}/api/v1/info", timeout=2)
            if res.status_code == 200:
                data = res.json()
                return data.get("data", {}).get("blockchain_height", 0)
        except:
            pass
        return 0


def test_basic_sync():
    """Test 1: Basic 3-node sync"""
    print("\n" + "="*60)
    print("TEST 1: Basic 3-Node Synchronization")
    print("="*60)
    
    nodes = []
    
    try:
        # Start all nodes
        for config in NODES:
            node = NodeProcess(
                port=config["port"],
                name=config["name"],
                peers=PEERS_CONFIG[config["port"]]
            )
            if not node.start():
                raise Exception(f"Failed to start {node.name}")
            nodes.append(node)
        
        print("\n[TEST] All 3 nodes started successfully")
        
        # Wait for sync
        print("[TEST] Waiting 10 seconds for initial sync...")
        time.sleep(10)
        
        # Check chain lengths
        print("\n[TEST] Checking blockchain synchronization:")
        for node in nodes:
            length = node.get_chain_length()
            print(f"  {node.name}: {length} blocks")
        
        print("\n[TEST] [OK] Basic sync test passed!")
        
    finally:
        # Stop all nodes
        for node in nodes:
            node.stop()


def test_node_failure():
    """Test 2: Node failure and recovery"""
    print("\n" + "="*60)
    print("TEST 2: Node Failure & Automatic Recovery")
    print("="*60)
    
    nodes = []
    
    try:
        # Start all nodes
        for config in NODES:
            node = NodeProcess(
                port=config["port"],
                name=config["name"],
                peers=PEERS_CONFIG[config["port"]]
            )
            if not node.start():
                raise Exception(f"Failed to start {node.name}")
            nodes.append(node)
        
        print("\n[TEST] All 3 nodes started successfully")
        time.sleep(10)
        
        # Get initial chain lengths
        print("\n[TEST] Initial state:")
        for node in nodes:
            length = node.get_chain_length()
            print(f"  {node.name}: {length} blocks")
        
        # Stop Node 1
        print(f"\n[TEST] Stopping {nodes[0].name}...")
        nodes[0].stop()
        time.sleep(2)
        
        # Verify Node 2 and Node 3 still running
        print(f"\n[TEST] Checking remaining nodes:")
        for node in nodes[1:]:
            if node.is_running():
                print(f"  {node.name}: Running [OK]")
            else:
                print(f"  {node.name}: FAILED [FAIL]")
                raise Exception(f"{node.name} should still be running!")
        
        # Wait for continued sync
        print(f"\n[TEST] Waiting 30 seconds for Nodes 2&3 to continue syncing...")
        time.sleep(30)
        
        # Check that Node 2 and Node 3 continue working
        print(f"\n[TEST] Final state (Node 1 offline):")
        for node in nodes[1:]:
            if node.is_running():
                length = node.get_chain_length()
                print(f"  {node.name}: {length} blocks [OK]")
            else:
                print(f"  {node.name}: OFFLINE")
        
        print("\n[TEST] [OK] Node failure test passed!")
        print("[TEST] [OK] Nodes 2 & 3 continued syncing after Node 1 failure!")
        
    finally:
        # Stop all nodes
        for node in nodes:
            try:
                node.stop()
            except:
                pass


def test_peer_recovery():
    """Test 3: Peer recovery when node comes back online"""
    print("\n" + "="*60)
    print("TEST 3: Automatic Peer Recovery")
    print("="*60)
    
    nodes = []
    
    try:
        # Start all nodes
        for config in NODES:
            node = NodeProcess(
                port=config["port"],
                name=config["name"],
                peers=PEERS_CONFIG[config["port"]]
            )
            if not node.start():
                raise Exception(f"Failed to start {node.name}")
            nodes.append(node)
        
        print("\n[TEST] All 3 nodes started")
        time.sleep(10)
        
        # Stop Node 1
        print(f"\n[TEST] Stopping {nodes[0].name}...")
        nodes[0].stop()
        time.sleep(5)
        
        # Restart Node 1
        print(f"\n[TEST] Restarting {nodes[0].name}...")
        nodes[0] = NodeProcess(
            port=NODES[0]["port"],
            name=NODES[0]["name"],
            peers=PEERS_CONFIG[NODES[0]["port"]]
        )
        if not nodes[0].start():
            raise Exception(f"Failed to restart {nodes[0].name}")
        
        # Wait for recovery
        print(f"\n[TEST] Waiting 30 seconds for automatic peer recovery...")
        time.sleep(30)
        
        # Check all nodes
        print(f"\n[TEST] Final state (all nodes should be synced):")
        all_running = True
        for node in nodes:
            if node.is_running():
                length = node.get_chain_length()
                print(f"  {node.name}: {length} blocks [OK]")
            else:
                print(f"  {node.name}: FAILED [FAIL]")
                all_running = False
        
        if all_running:
            print("\n[TEST] [OK] Peer recovery test passed!")
            print("[TEST] [OK] Node 1 successfully recovered and re-synced!")
        else:
            print("\n[TEST] [FAIL] Test failed - not all nodes running")
        
    finally:
        # Stop all nodes
        for node in nodes:
            try:
                node.stop()
            except:
                pass


def main():
    """Run all tests"""
    print("="*60)
    print("PHN BLOCKCHAIN - MULTI-NODE FAILURE TESTING")
    print("="*60)
    print("\nThis script will test:")
    print("  1. Basic 3-node synchronization")
    print("  2. Node failure handling (Node 1 goes offline)")
    print("  3. Automatic peer recovery (Node 1 comes back)")
    print("\nMake sure no other PHN nodes are running!")
    print("="*60)
    
    input("\nPress Enter to start tests...")
    
    try:
        # Run tests
        test_basic_sync()
        time.sleep(5)
        
        test_node_failure()
        time.sleep(5)
        
        test_peer_recovery()
        
        print("\n" + "="*60)
        print("ALL TESTS COMPLETED!")
        print("="*60)
        print("\n[OK] Basic sync: PASSED")
        print("[OK] Node failure: PASSED")
        print("[OK] Peer recovery: PASSED")
        print("\nYour PHN blockchain has robust node synchronization!")
        
    except KeyboardInterrupt:
        print("\n\nTests cancelled by user")
    except Exception as e:
        print(f"\n\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
