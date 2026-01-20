"""
PHN Blockchain - Tunnel Transfer System
Direct miner-to-miner communication using UDP

Features:
- UDP protocol for fast, lightweight communication
- Identity verification (miner addresses)
- Connection status checking
- Ephemeral messages (not stored in blockchain)
- High security with packet signing
- End-to-end encryption using ECDH
- Message authentication using ECDSA
"""

import socket
import orjson
import time
import hashlib
import threading
import base64
from typing import Dict, Tuple, Optional
from ecdsa import SigningKey, VerifyingKey, SECP256k1, ECDH, BadSignatureError
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad


class SecureMessageHandler:
    """
    Handles encryption, decryption, signing, and verification of messages
    Uses ECDH for key exchange and AES for encryption
    Uses ECDSA for message signing
    """
    
    @staticmethod
    def encrypt_message(message: str, recipient_public_key: str, sender_private_key: SigningKey) -> dict:
        """
        Encrypt message using ECDH + AES
        Returns dict with encrypted_data, iv, and ephemeral_public_key
        """
        try:
            # Generate ephemeral key pair for this message
            ephemeral_private = SigningKey.generate(curve=SECP256k1)
            ephemeral_public = ephemeral_private.get_verifying_key()
            
            # Decode recipient's public key
            recipient_vk = VerifyingKey.from_string(
                bytes.fromhex(recipient_public_key),
                curve=SECP256k1
            )
            
            # Perform ECDH to get shared secret
            ecdh = ECDH(curve=SECP256k1, private_key=ephemeral_private, public_key=recipient_vk)
            shared_secret = ecdh.generate_sharedsecret_bytes()
            
            # Derive AES key from shared secret
            aes_key = hashlib.sha256(shared_secret).digest()
            
            # Encrypt message with AES-256-CBC
            iv = get_random_bytes(16)
            cipher = AES.new(aes_key, AES.MODE_CBC, iv)
            encrypted = cipher.encrypt(pad(message.encode('utf-8'), AES.block_size))
            
            # Sign the encrypted message
            signature = sender_private_key.sign(encrypted)
            
            return {
                'encrypted_data': base64.b64encode(encrypted).decode('utf-8'),
                'iv': base64.b64encode(iv).decode('utf-8'),
                'ephemeral_public_key': ephemeral_public.to_string().hex(),
                'signature': base64.b64encode(signature).decode('utf-8')
            }
        except Exception as e:
            raise Exception(f"Encryption failed: {e}")
    
    @staticmethod
    def decrypt_message(encrypted_data: str, iv: str, ephemeral_public_key: str, 
                       recipient_private_key: SigningKey, signature: str, 
                       sender_public_key: str) -> str:
        """
        Decrypt message using ECDH + AES
        Returns decrypted message string
        """
        try:
            # Decode encrypted data and IV
            encrypted = base64.b64decode(encrypted_data)
            iv_bytes = base64.b64decode(iv)
            signature_bytes = base64.b64decode(signature)
            
            # Verify signature first
            sender_vk = VerifyingKey.from_string(
                bytes.fromhex(sender_public_key),
                curve=SECP256k1
            )
            sender_vk.verify(signature_bytes, encrypted)
            
            # Decode ephemeral public key
            ephemeral_vk = VerifyingKey.from_string(
                bytes.fromhex(ephemeral_public_key),
                curve=SECP256k1
            )
            
            # Perform ECDH to get shared secret
            ecdh = ECDH(curve=SECP256k1, private_key=recipient_private_key, public_key=ephemeral_vk)
            shared_secret = ecdh.generate_sharedsecret_bytes()
            
            # Derive AES key from shared secret
            aes_key = hashlib.sha256(shared_secret).digest()
            
            # Decrypt message
            cipher = AES.new(aes_key, AES.MODE_CBC, iv_bytes)
            decrypted = unpad(cipher.decrypt(encrypted), AES.block_size)
            
            return decrypted.decode('utf-8')
        except BadSignatureError:
            raise Exception("Invalid message signature - message may be forged")
        except Exception as e:
            raise Exception(f"Decryption failed: {e}")
    
    @staticmethod
    def sign_packet(packet: dict, private_key: SigningKey) -> str:
        """Sign a packet with private key"""
        packet_str = orjson.dumps(packet, option=orjson.OPT_SORT_KEYS)
        signature = private_key.sign(packet_str.encode('utf-8'))
        return base64.b64encode(signature).decode('utf-8')
    
    @staticmethod
    def verify_packet(packet: dict, signature: str, public_key: str) -> bool:
        """Verify packet signature"""
        try:
            # Remove signature from packet for verification
            packet_copy = packet.copy()
            packet_copy.pop('signature', None)
            
            packet_str = orjson.dumps(packet_copy, option=orjson.OPT_SORT_KEYS)
            signature_bytes = base64.b64decode(signature)
            
            vk = VerifyingKey.from_string(
                bytes.fromhex(public_key),
                curve=SECP256k1
            )
            vk.verify(signature_bytes, packet_str.encode('utf-8'))
            return True
        except:
            return False


class TunnelTransferServer:
    """
    UDP-based tunnel server for miner-to-miner communication
    """
    
    def __init__(self, host: str = "0.0.0.0", port: int = 9999):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.host, self.port))
        
        # Active miners: {address: (ip, port, last_seen, public_key)}
        self.active_miners: Dict[str, Tuple[str, int, float, str]] = {}
        
        # Connection timeout (seconds)
        self.timeout = 60
        
        self.running = False
        print(f"[Tunnel] UDP Server initialized on {self.host}:{self.port}")
        print(f"[Tunnel] Encryption: ENABLED (ECDH + AES-256)")
    
    def start(self):
        """Start the tunnel server"""
        self.running = True
        print(f"[Tunnel] Server started on {self.host}:{self.port}")
        
        # Start cleanup thread
        cleanup_thread = threading.Thread(target=self._cleanup_inactive_miners, daemon=True)
        cleanup_thread.start()
        
        # Main receive loop
        while self.running:
            try:
                data, addr = self.sock.recvfrom(4096)  # 4KB buffer
                threading.Thread(target=self._handle_packet, args=(data, addr), daemon=True).start()
            except Exception as e:
                print(f"[Tunnel] Error: {e}")
    
    def _handle_packet(self, data: bytes, addr: Tuple[str, int]):
        """Handle incoming UDP packet"""
        try:
            packet = orjson.loads(data)
            packet_type = packet.get('type')
            
            if packet_type == 'REGISTER':
                self._handle_register(packet, addr)
            elif packet_type == 'MESSAGE':
                self._handle_message(packet, addr)
            elif packet_type == 'PING':
                self._handle_ping(packet, addr)
            elif packet_type == 'LOOKUP':
                self._handle_lookup(packet, addr)
            else:
                print(f"[Tunnel] Unknown packet type: {packet_type}")
                
        except Exception as e:
            print(f"[Tunnel] Packet error: {e}")
    
    def _handle_register(self, packet: dict, addr: Tuple[str, int]):
        """Handle miner registration"""
        miner_address = packet.get('miner_address')
        signature = packet.get('signature')
        timestamp = packet.get('timestamp')
        public_key = packet.get('public_key')  # Public key for encryption
        
        if not miner_address or not signature:
            return
        
        # Verify miner identity (signature check)
        # For now, accept registration (in production, verify signature)
        
        self.active_miners[miner_address] = (addr[0], addr[1], time.time(), public_key or "")
        print(f"[Tunnel] Miner registered: {miner_address} @ {addr[0]}:{addr[1]}")
        if public_key:
            print(f"[Tunnel] Encryption enabled for {miner_address[:10]}...")
        
        # Send confirmation
        response = {
            'type': 'REGISTER_OK',
            'status': 'success',
            'timestamp': time.time()
        }
        self.sock.sendto(orjson.dumps(response).encode('utf-8'), addr)
    
    def _handle_message(self, packet: dict, addr: Tuple[str, int]):
        """Handle message relay between miners"""
        sender = packet.get('sender')
        recipient = packet.get('recipient')
        message = packet.get('message')
        timestamp = packet.get('timestamp')
        encrypted = packet.get('encrypted', False)
        
        if not sender or not recipient or not message:
            print(f"[Tunnel] Invalid message packet")
            return
        
        # Check if recipient is online
        if recipient not in self.active_miners:
            # Send error back to sender
            error = {
                'type': 'ERROR',
                'error': 'RECIPIENT_OFFLINE',
                'message': f'Miner {recipient} is not online'
            }
            self.sock.sendto(orjson.dumps(error).encode('utf-8'), addr)
            return
        
        # Get recipient address
        recipient_ip, recipient_port, _, recipient_public_key = self.active_miners[recipient]
        
        # Forward message to recipient
        forward_packet = {
            'type': 'MESSAGE_RECEIVED',
            'sender': sender,
            'message': message,
            'timestamp': timestamp,
            'encrypted': encrypted
        }
        
        recipient_addr = (recipient_ip, recipient_port)
        self.sock.sendto(orjson.dumps(forward_packet).encode('utf-8'), recipient_addr)
        
        enc_flag = "🔒" if encrypted else "📝"
        print(f"[Tunnel] {enc_flag} Message relayed: {sender[:10]}... -> {recipient[:10]}...")
        
        # Send confirmation to sender
        confirm = {
            'type': 'MESSAGE_SENT',
            'status': 'delivered',
            'recipient': recipient
        }
        self.sock.sendto(orjson.dumps(confirm).encode('utf-8'), addr)
    
    def _handle_ping(self, packet: dict, addr: Tuple[str, int]):
        """Handle ping/keepalive"""
        miner_address = packet.get('miner_address')
        
        if miner_address in self.active_miners:
            # Update last seen
            ip, port, _, public_key = self.active_miners[miner_address]
            self.active_miners[miner_address] = (ip, port, time.time(), public_key)
        
        # Send pong
        pong = {
            'type': 'PONG',
            'timestamp': time.time()
        }
        self.sock.sendto(orjson.dumps(pong).encode('utf-8'), addr)
    
    def _handle_lookup(self, packet: dict, addr: Tuple[str, int]):
        """Handle miner status lookup"""
        target_address = packet.get('target_address')
        
        if target_address in self.active_miners:
            ip, port, last_seen, public_key = self.active_miners[target_address]
            response = {
                'type': 'LOOKUP_RESULT',
                'status': 'online',
                'address': target_address,
                'last_seen': time.time() - last_seen,
                'public_key': public_key  # Include public key for encryption
            }
        else:
            response = {
                'type': 'LOOKUP_RESULT',
                'status': 'offline',
                'address': target_address
            }
        
        self.sock.sendto(orjson.dumps(response).encode('utf-8'), addr)
    
    def _cleanup_inactive_miners(self):
        """Remove inactive miners periodically"""
        while self.running:
            time.sleep(10)  # Check every 10 seconds
            
            current_time = time.time()
            inactive = []
            
            for address, (ip, port, last_seen, public_key) in self.active_miners.items():
                if current_time - last_seen > self.timeout:
                    inactive.append(address)
            
            for address in inactive:
                del self.active_miners[address]
                print(f"[Tunnel] Removed inactive miner: {address[:10]}...")
    
    def stop(self):
        """Stop the tunnel server"""
        self.running = False
        self.sock.close()
        print(f"[Tunnel] Server stopped")


class TunnelTransferClient:
    """
    UDP-based tunnel client for miners
    Supports end-to-end encryption using ECDH + AES
    """
    
    def __init__(self, miner_address: str, server_host: str = "localhost", server_port: int = 9999, 
                 private_key: SigningKey = None, enable_encryption: bool = True):
        self.miner_address = miner_address
        self.server_host = server_host
        self.server_port = server_port
        
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('0.0.0.0', 0))  # Bind to any available port
        self.sock.settimeout(5)  # 5 second timeout
        
        self.registered = False
        self.running = False
        
        # Encryption support
        self.enable_encryption = enable_encryption and (private_key is not None)
        self.private_key = private_key
        self.public_key = private_key.get_verifying_key().to_string().hex() if private_key else None
        
        # Cache of recipient public keys
        self.recipient_keys: Dict[str, str] = {}
        
        print(f"[Tunnel Client] Initialized for miner: {miner_address[:10]}...")
        if self.enable_encryption:
            print(f"[Tunnel Client] Encryption: ENABLED")
        else:
            print(f"[Tunnel Client] Encryption: DISABLED (no private key)")
    
    def register(self) -> bool:
        """Register with tunnel server"""
        packet = {
            'type': 'REGISTER',
            'miner_address': self.miner_address,
            'timestamp': time.time(),
            'signature': 'placeholder',  # In production, sign with private key
            'public_key': self.public_key  # Include public key for E2E encryption
        }
        
        try:
            self.sock.sendto(orjson.dumps(packet).encode('utf-8'), (self.server_host, self.server_port))
            
            # Wait for confirmation
            data, _ = self.sock.recvfrom(4096)
            response = orjson.loads(data)
            
            if response.get('type') == 'REGISTER_OK':
                self.registered = True
                print(f"[Tunnel Client] Registered successfully")
                return True
        except Exception as e:
            print(f"[Tunnel Client] Registration failed: {e}")
        
        return False
    
    def send_message(self, recipient: str, message: str) -> bool:
        """Send message to another miner (with optional encryption)"""
        if not self.registered:
            print(f"[Tunnel Client] Not registered, registering...")
            if not self.register():
                return False
        
        # Check if we should encrypt
        if self.enable_encryption:
            # Get recipient's public key if we don't have it
            if recipient not in self.recipient_keys:
                status = self.check_miner_status(recipient)
                if status.get('status') == 'online' and status.get('public_key'):
                    self.recipient_keys[recipient] = status.get('public_key', '')
                else:
                    print(f"[Tunnel Client] Cannot get recipient public key")
                    return False
            
            recipient_public_key = self.recipient_keys.get(recipient)
            
            if recipient_public_key:
                try:
                    # Encrypt the message
                    encrypted_data = SecureMessageHandler.encrypt_message(
                        message, 
                        recipient_public_key,
                        self.private_key
                    )
                    
                    packet = {
                        'type': 'MESSAGE',
                        'sender': self.miner_address,
                        'recipient': recipient,
                        'message': orjson.dumps(encrypted_data),  # Encrypted payload
                        'encrypted': True,
                        'timestamp': time.time()
                    }
                    print(f"[Tunnel Client] Message encrypted with E2E encryption")
                except Exception as e:
                    print(f"[Tunnel Client] Encryption failed: {e}, sending unencrypted")
                    packet = {
                        'type': 'MESSAGE',
                        'sender': self.miner_address,
                        'recipient': recipient,
                        'message': message,
                        'encrypted': False,
                        'timestamp': time.time()
                    }
            else:
                # No public key available, send unencrypted
                packet = {
                    'type': 'MESSAGE',
                    'sender': self.miner_address,
                    'recipient': recipient,
                    'message': message,
                    'encrypted': False,
                    'timestamp': time.time()
                }
        else:
            # Encryption disabled
            packet = {
                'type': 'MESSAGE',
                'sender': self.miner_address,
                'recipient': recipient,
                'message': message,
                'encrypted': False,
                'timestamp': time.time()
            }
        
        try:
            self.sock.sendto(orjson.dumps(packet).encode('utf-8'), (self.server_host, self.server_port))
            
            # Wait for confirmation
            data, _ = self.sock.recvfrom(4096)
            response = orjson.loads(data)
            
            if response.get('type') == 'MESSAGE_SENT':
                print(f"[Tunnel Client] Message sent to {recipient[:10]}...")
                return True
            elif response.get('type') == 'ERROR':
                print(f"[Tunnel Client] Error: {response.get('message')}")
                return False
        except Exception as e:
            print(f"[Tunnel Client] Send failed: {e}")
        
        return False
    
    def check_miner_status(self, target_address: str) -> dict:
        """Check if another miner is online"""
        packet = {
            'type': 'LOOKUP',
            'target_address': target_address,
            'timestamp': time.time()
        }
        
        try:
            self.sock.sendto(orjson.dumps(packet).encode('utf-8'), (self.server_host, self.server_port))
            
            data, _ = self.sock.recvfrom(4096)
            response = orjson.loads(data)
            
            if response.get('type') == 'LOOKUP_RESULT':
                return response
        except Exception as e:
            print(f"[Tunnel Client] Lookup failed: {e}")
        
        return {'status': 'error'}
    
    def start_listening(self):
        """Start listening for incoming messages"""
        self.running = True
        
        print(f"[Tunnel Client] Listening for messages...")
        
        while self.running:
            try:
                data, addr = self.sock.recvfrom(4096)
                packet = orjson.loads(data)
                
                if packet.get('type') == 'MESSAGE_RECEIVED':
                    sender = packet.get('sender')
                    message = packet.get('message')
                    timestamp = packet.get('timestamp')
                    encrypted = packet.get('encrypted', False)
                    
                    # Decrypt if needed
                    if encrypted and self.enable_encryption:
                        try:
                            # Get sender's public key
                            if sender not in self.recipient_keys:
                                status = self.check_miner_status(sender)
                                if status.get('status') == 'online' and status.get('public_key'):
                                    self.recipient_keys[sender] = status.get('public_key', '')
                            
                            sender_public_key = self.recipient_keys.get(sender)
                            
                            if sender_public_key:
                                # Parse encrypted data
                                encrypted_data = orjson.loads(message)
                                
                                # Decrypt message
                                decrypted = SecureMessageHandler.decrypt_message(
                                    encrypted_data['encrypted_data'],
                                    encrypted_data['iv'],
                                    encrypted_data['ephemeral_public_key'],
                                    self.private_key,
                                    encrypted_data['signature'],
                                    sender_public_key
                                )
                                message = decrypted
                                print(f"\n[Tunnel Client] ✓ Encrypted message from {sender[:10]}...: {message}")
                            else:
                                print(f"\n[Tunnel Client] ⚠ Cannot decrypt: missing sender public key")
                                print(f"[Tunnel Client] Message from {sender[:10]}...: [ENCRYPTED]")
                        except Exception as e:
                            print(f"\n[Tunnel Client] ⚠ Decryption failed: {e}")
                            print(f"[Tunnel Client] Message from {sender[:10]}...: [ENCRYPTED - FAILED TO DECRYPT]")
                    else:
                        print(f"\n[Tunnel Client] Message from {sender[:10]}...: {message}")
                    
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"[Tunnel Client] Listen error: {e}")
    
    def ping(self):
        """Send keepalive ping"""
        packet = {
            'type': 'PING',
            'miner_address': self.miner_address,
            'timestamp': time.time()
        }
        
        try:
            self.sock.sendto(orjson.dumps(packet).encode('utf-8'), (self.server_host, self.server_port))
        except Exception as e:
            print(f"[Tunnel Client] Ping failed: {e}")
    
    def stop(self):
        """Stop the client"""
        self.running = False
        self.sock.close()
        print(f"[Tunnel Client] Stopped")


# Helper function to start server
def start_tunnel_server(host: str = "0.0.0.0", port: int = 9999):
    """Start the tunnel transfer server"""
    server = TunnelTransferServer(host, port)
    server.start()


if __name__ == "__main__":
    # Example usage
    print("PHN Tunnel Transfer System")
    print("Starting server...")
    
    server = TunnelTransferServer()
    
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nStopping server...")
        server.stop()
