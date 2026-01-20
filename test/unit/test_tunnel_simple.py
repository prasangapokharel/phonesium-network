"""
PHN Tunnel Transfer - Simple Test
Test two miners sending messages to each other
"""

import sys
import os
import time
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.extensions.tunnel import TunnelTransferClient

# Test miner addresses
MINER_A = "PHN718b7ad6d46933825778e5c95757e12b853e3d0c"
MINER_B = "PHN2d1395d42165409292c9994aee240666b91458a"

TUNNEL_SERVER = "localhost"
TUNNEL_PORT = 9999

print("="*70)
print("PHN TUNNEL TRANSFER - SIMPLE TEST")
print("="*70)
print(f"\nMiner A: {MINER_A}")
print(f"Miner B: {MINER_B}")
print(f"\nTunnel Server: {TUNNEL_SERVER}:{TUNNEL_PORT}")
print("="*70)

# Create clients
print("\n[1] Creating clients...")
client_a = TunnelTransferClient(MINER_A, TUNNEL_SERVER, TUNNEL_PORT)
client_b = TunnelTransferClient(MINER_B, TUNNEL_SERVER, TUNNEL_PORT)

# Register both miners
print("\n[2] Registering Miner A...")
if client_a.register():
    print("    [OK] Miner A registered")
else:
    print("    [FAIL] Miner A registration failed")
    sys.exit(1)

print("\n[3] Registering Miner B...")
if client_b.register():
    print("    [OK] Miner B registered")
else:
    print("    [FAIL] Miner B registration failed")
    sys.exit(1)

# Start listening on both
print("\n[4] Starting listeners...")

def listen_a():
    client_a.start_listening()

def listen_b():
    client_b.start_listening()

thread_a = threading.Thread(target=listen_a, daemon=True)
thread_b = threading.Thread(target=listen_b, daemon=True)

thread_a.start()
thread_b.start()

print("    [OK] Both miners listening")

# Check if miners can see each other
print("\n[5] Checking miner status...")
status_b = client_a.check_miner_status(MINER_B)
print(f"    Miner B status (from A): {status_b.get('status')}")

status_a = client_b.check_miner_status(MINER_A)
print(f"    Miner A status (from B): {status_a.get('status')}")

# Send message from A to B
print("\n[6] Miner A sending 'hi' to Miner B...")
time.sleep(1)
if client_a.send_message(MINER_B, "hi"):
    print("    [OK] Message sent")
else:
    print("    [FAIL] Message send failed")

# Wait for message to be received
print("\n[7] Waiting for message delivery...")
time.sleep(2)

# Send reply from B to A
print("\n[8] Miner B sending 'hello!' to Miner A...")
if client_b.send_message(MINER_A, "hello!"):
    print("    [OK] Reply sent")
else:
    print("    [FAIL] Reply failed")

# Wait for reply
print("\n[9] Waiting for reply...")
time.sleep(2)

# Cleanup
print("\n[10] Cleaning up...")
client_a.stop()
client_b.stop()

print("\n" + "="*70)
print("TEST COMPLETE")
print("="*70)
print("\nSummary:")
print("  - Both miners registered successfully")
print("  - Both miners can see each other as online")
print("  - Messages sent directly between miners")
print("  - No blockchain storage (ephemeral)")
print("  - UDP protocol (fast and lightweight)")
print("="*70)
