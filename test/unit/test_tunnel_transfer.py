"""
PHN Tunnel Transfer - Test Script
Test sending messages between two miners
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

def test_miner_a():
    """Simulate Miner A"""
    print("="*60)
    print("MINER A - Starting")
    print(f"Address: {MINER_A}")
    print("="*60)
    
    client = TunnelTransferClient(MINER_A, TUNNEL_SERVER, TUNNEL_PORT)
    
    # Register
    print("[Miner A] Registering with tunnel server...")
    if not client.register():
        print("[Miner A] FAILED to register")
        return
    
    print("[Miner A] Registered successfully!")
    
    # Start listening in background
    listen_thread = threading.Thread(target=client.start_listening, daemon=True)
    listen_thread.start()
    
    # Wait a bit for Miner B to register
    time.sleep(2)
    
    # Check if Miner B is online
    print(f"[Miner A] Checking if Miner B is online...")
    status = client.check_miner_status(MINER_B)
    print(f"[Miner A] Miner B status: {status.get('status')}")
    
    if status.get('status') == 'online':
        # Send message
        print(f"[Miner A] Sending 'hi' to Miner B...")
        if client.send_message(MINER_B, "hi"):
            print(f"[Miner A] Message sent successfully!")
        else:
            print(f"[Miner A] Failed to send message")
    else:
        print(f"[Miner A] Miner B is offline, cannot send message")
    
    # Wait for response
    print("[Miner A] Waiting for messages... (10 seconds)")
    time.sleep(10)
    
    client.stop()
    print("[Miner A] Stopped")

def test_miner_b():
    """Simulate Miner B"""
    print("="*60)
    print("MINER B - Starting")
    print(f"Address: {MINER_B}")
    print("="*60)
    
    client = TunnelTransferClient(MINER_B, TUNNEL_SERVER, TUNNEL_PORT)
    
    # Register
    print("[Miner B] Registering with tunnel server...")
    if not client.register():
        print("[Miner B] FAILED to register")
        return
    
    print("[Miner B] Registered successfully!")
    
    # Start listening in background
    listen_thread = threading.Thread(target=client.start_listening, daemon=True)
    listen_thread.start()
    
    # Wait for messages from Miner A
    print("[Miner B] Waiting for messages... (15 seconds)")
    time.sleep(5)
    
    # After receiving, send reply
    print(f"[Miner B] Sending 'hello!' to Miner A...")
    if client.send_message(MINER_A, "hello!"):
        print(f"[Miner B] Reply sent successfully!")
    
    time.sleep(5)
    
    client.stop()
    print("[Miner B] Stopped")

def run_full_test():
    """Run complete test with both miners"""
    print("\n" + "="*60)
    print("PHN TUNNEL TRANSFER - FULL TEST")
    print("="*60)
    print("\nMake sure the tunnel server is running first:")
    print("  python -m app.core.tunnel_transfer")
    print("\nPress Enter to start test...")
    input()
    
    # Start Miner B first (receiver)
    miner_b_thread = threading.Thread(target=test_miner_b, daemon=True)
    miner_b_thread.start()
    
    time.sleep(1)
    
    # Start Miner A (sender)
    miner_a_thread = threading.Thread(target=test_miner_a, daemon=True)
    miner_a_thread.start()
    
    # Wait for both to finish
    miner_b_thread.join()
    miner_a_thread.join()
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)

if __name__ == "__main__":
    run_full_test()
