#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test encrypted tunnel transfer system
Tests end-to-end encryption using ECDH + AES-256
"""

import sys
import os
import time
import orjson
import threading
from pathlib import Path

# Fix Windows console encoding
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.extensions.tunnel import TunnelTransferServer, TunnelTransferClient, SecureMessageHandler
from ecdsa import SigningKey, SECP256k1


def test_secure_message_handler():
    """Test the encryption/decryption functions"""
    print("\n" + "=" * 70)
    print("TEST 1: SecureMessageHandler - Encryption/Decryption")
    print("=" * 70)
    
    # Generate key pairs for sender and recipient
    sender_private = SigningKey.generate(curve=SECP256k1)
    sender_public = sender_private.get_verifying_key().to_string().hex()
    
    recipient_private = SigningKey.generate(curve=SECP256k1)
    recipient_public = recipient_private.get_verifying_key().to_string().hex()
    
    # Test message
    original_message = "Hello, this is a secret message! "
    print(f"\n[Original Message] {original_message}")
    
    # Encrypt
    print("[Encrypting...] Using ECDH + AES-256")
    encrypted_data = SecureMessageHandler.encrypt_message(
        original_message,
        recipient_public,
        sender_private
    )
    
    print(f"[Encrypted Data] {len(orjson.dumps(encrypted_data))} bytes")
    print(f"  - IV: {encrypted_data['iv'][:20]}...")
    print(f"  - Encrypted: {encrypted_data['encrypted_data'][:40]}...")
    print(f"  - Ephemeral Key: {encrypted_data['ephemeral_public_key'][:40]}...")
    print(f"  - Signature: {encrypted_data['signature'][:40]}...")
    
    # Decrypt
    print("[Decrypting...] Verifying signature and decrypting")
    decrypted_message = SecureMessageHandler.decrypt_message(
        encrypted_data['encrypted_data'],
        encrypted_data['iv'],
        encrypted_data['ephemeral_public_key'],
        recipient_private,
        encrypted_data['signature'],
        sender_public
    )
    
    print(f"[Decrypted Message] {decrypted_message}")
    
    # Verify
    if decrypted_message == original_message:
        print("[OK] TEST PASSED: Message encrypted and decrypted successfully")
        return True
    else:
        print("[FAIL] TEST FAILED: Decrypted message doesn't match original")
        return False


def test_encrypted_tunnel_transfer():
    """Test full tunnel transfer with encryption"""
    print("\n" + "=" * 70)
    print("TEST 2: Encrypted Tunnel Transfer (E2E)")
    print("=" * 70)
    
    # Start tunnel server
    print("\n[Starting] Tunnel server...")
    server = TunnelTransferServer(host="localhost", port=9998)
    server_thread = threading.Thread(target=server.start, daemon=True)
    server_thread.start()
    time.sleep(1)
    
    # Load two wallets for testing
    wallet_dir = Path(__file__).parent.parent / "user" / "wallets"
    wallets = list(wallet_dir.glob("*.json"))
    
    if len(wallets) < 2:
        print("[FAIL] TEST SKIPPED: Need at least 2 wallets in user/wallets/")
        server.stop()
        return False
    
    # Load wallet 1
    with open(wallets[0]) as f:
        wallet1 = orjson.loads(f.read())
    
    address1 = wallet1['address']
    private_key1 = SigningKey.from_string(
        bytes.fromhex(wallet1['private_key']),
        curve=SECP256k1
    )
    
    # Load wallet 2
    with open(wallets[1]) as f:
        wallet2 = orjson.loads(f.read())
    
    address2 = wallet2['address']
    private_key2 = SigningKey.from_string(
        bytes.fromhex(wallet2['private_key']),
        curve=SECP256k1
    )
    
    print(f"\n[Miner 1] {address1[:20]}...")
    print(f"[Miner 2] {address2[:20]}...")
    
    # Create clients with encryption enabled
    print("\n[Creating] Encrypted tunnel clients...")
    client1 = TunnelTransferClient(
        address1,
        server_host="localhost",
        server_port=9998,
        private_key=private_key1,
        enable_encryption=True
    )
    
    client2 = TunnelTransferClient(
        address2,
        server_host="localhost",
        server_port=9998,
        private_key=private_key2,
        enable_encryption=True
    )
    
    # Register both clients
    print("\n[Registering] Clients with tunnel server...")
    if not client1.register():
        print("[FAIL] TEST FAILED: Client 1 registration failed")
        server.stop()
        return False
    
    if not client2.register():
        print("[FAIL] TEST FAILED: Client 2 registration failed")
        server.stop()
        return False
    
    time.sleep(0.5)
    
    # Send encrypted message from client1 to client2
    print("\n[Sending] Encrypted message from Miner 1 to Miner 2...")
    test_message = "This is an encrypted test message! "
    
    # Start listening on client2
    messages_received = []
    
    def listen_client2():
        try:
            data, addr = client2.sock.recvfrom(65536)
            packet = orjson.loads(data.decode('utf-8'))
            
            if packet.get('type') == 'MESSAGE_RECEIVED':
                sender = packet.get('sender')
                message = packet.get('message')
                encrypted = packet.get('encrypted', False)
                
                print(f"\n[Client 2 Received] Encrypted={encrypted}")
                
                if encrypted:
                    # Decrypt
                    encrypted_data = orjson.loads(message)
                    
                    # Get sender public key
                    status = client2.check_miner_status(sender)
                    sender_public_key = status.get('public_key')
                    
                    decrypted = SecureMessageHandler.decrypt_message(
                        encrypted_data['encrypted_data'],
                        encrypted_data['iv'],
                        encrypted_data['ephemeral_public_key'],
                        private_key2,
                        encrypted_data['signature'],
                        sender_public_key
                    )
                    messages_received.append(decrypted)
                    print(f"[Decrypted] {decrypted}")
                else:
                    messages_received.append(message)
                    print(f"[Plain Text] {message}")
        except Exception as e:
            print(f"[Error] {e}")
            import traceback
            traceback.print_exc()
    
    listen_thread = threading.Thread(target=listen_client2, daemon=True)
    listen_thread.start()
    
    # Send the message
    result = client1.send_message(address2, test_message)
    
    if not result:
        print("[FAIL] TEST FAILED: Message send failed")
        server.stop()
        return False
    
    # Wait for message to be received
    time.sleep(2)
    
    # Check if message was received and decrypted
    if len(messages_received) > 0 and messages_received[0] == test_message:
        print(f"\n[OK] TEST PASSED: Encrypted message sent and decrypted successfully")
        print(f"  Original: {test_message}")
        print(f"  Received: {messages_received[0]}")
        server.stop()
        return True
    else:
        print(f"\n[FAIL] TEST FAILED: Message not received or decryption failed")
        print(f"  Expected: {test_message}")
        print(f"  Received: {messages_received}")
        server.stop()
        return False


def main():
    """Run all encryption tests"""
    print("=" * 70)
    print("PHN BLOCKCHAIN - ENCRYPTED TUNNEL TRANSFER TESTS")
    print("=" * 70)
    
    results = []
    
    # Test 1: Basic encryption/decryption
    try:
        results.append(("SecureMessageHandler", test_secure_message_handler()))
    except Exception as e:
        print(f"\n[FAIL] TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        results.append(("SecureMessageHandler", False))
    
    # Test 2: Full tunnel transfer with encryption
    try:
        results.append(("Encrypted Tunnel Transfer", test_encrypted_tunnel_transfer()))
    except Exception as e:
        print(f"\n[FAIL] TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Encrypted Tunnel Transfer", False))
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    for name, passed in results:
        status = "[OK] PASS" if passed else "[FAIL] FAIL"
        print(f"{status} - {name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print("=" * 70)
    
    return all(p for _, p in results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
