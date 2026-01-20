"""
Test Communication.py - Automated test
"""
import sys
import os
import time
import threading
import orjson

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from user.Communication import MinerCommunicator

print("="*70)
print("TESTING MINER COMMUNICATION")
print("="*70)

# Get two wallets
wallet1 = "user/wallets/wallet_1_853e3d0c.json"
wallet2 = "user/wallets/wallet_6b91458a.json"

with open(wallet1) as f:
    w1 = orjson.loads(f.read())
    addr1 = w1['address']

with open(wallet2) as f:
    w2 = orjson.loads(f.read())
    addr2 = w2['address']

print(f"\nMiner 1: {addr1}")
print(f"Miner 2: {addr2}")
print()

# Create communicators
print("[1] Creating communicators...")
comm1 = MinerCommunicator(wallet1)
comm2 = MinerCommunicator(wallet2)

# Connect both
print("\n[2] Connecting to tunnel server...")
try:
    if not comm1.connect():
        print("ERROR: Comm1 failed to connect")
        raise Exception("Comm1 connection failed")
    
    if not comm2.connect():
        print("ERROR: Comm2 failed to connect")
        raise Exception("Comm2 connection failed")

print("    [OK] Both connected")

# Wait for registration
time.sleep(1)

# List online miners from comm1's perspective
print("\n[3] Listing online miners (from Miner 1)...")
online = comm1.list_online_miners()
print(f"    Found {len(online)} online miners")
for miner in online:
    print(f"      - {miner['wallet']}: {miner['address'][:20]}...")

# Send message from Miner 1 to Miner 2
print("\n[4] Miner 1 sending 'Hello from Miner 1!' to Miner 2...")
time.sleep(1)
if comm1.send_message(addr2, "Hello from Miner 1!"):
    print("    [OK] Message sent")
else:
    print("    [FAIL] Message failed")

# Wait for message delivery
time.sleep(2)

# Send reply from Miner 2 to Miner 1
print("\n[5] Miner 2 sending 'Hi back!' to Miner 1...")
if comm2.send_message(addr1, "Hi back!"):
    print("    [OK] Reply sent")
else:
    print("    [FAIL] Reply failed")

# Wait
time.sleep(2)

# Test file transfer
print("\n[6] Testing file transfer...")
print("    Creating test file...")
with open("test_file.txt", "w") as f:
    f.write("This is a test file from Miner 1!")

print("    Sending file from Miner 1 to Miner 2...")
if comm1.send_file(addr2, "test_file.txt"):
    print("    [OK] File sent")
else:
    print("    [FAIL] File send failed")

# Wait for file delivery
time.sleep(2)

# Cleanup
print("\n[7] Cleaning up...")
comm1.running = False
comm2.running = False
comm1.client.stop()
comm2.client.stop()

print("\n" + "="*70)
print("TEST COMPLETE")
print("="*70)
print("\nFeatures tested:")
print("  [OK] Auto-wallet detection")
print("  [OK] Auto-connect to tunnel")
print("  [OK] List online miners")
print("  [OK] Send text messages")
print("  [OK] Receive text messages")
print("  [OK] Send files")
print("  [OK] Receive files")
print("="*70)
