#!/usr/bin/env python3
"""
PHN Miner Communication - Easy Chat & File Transfer
Auto-discovers other miners and enables direct communication
No manual configuration needed!
Supports end-to-end encryption using ECDH + AES-256
"""

import sys
import os
import orjson
import time
import threading
import base64
from pathlib import Path
from ecdsa import SigningKey, SECP256k1

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.tunnel_transfer import TunnelTransferClient

# Auto-detect tunnel server from environment or use default
TUNNEL_SERVER = os.getenv("TUNNEL_SERVER", "localhost")
TUNNEL_PORT = int(os.getenv("TUNNEL_PORT", "9999"))

class MinerCommunicator:
    """
    Easy communication interface for miners
    Features:
    - Auto-detect miner address from wallet
    - List online miners
    - Send text messages
    - Send files
    - Receive messages and files
    """
    
    def __init__(self, wallet_file: str = None, enable_encryption: bool = True):
        """Initialize communicator with wallet"""
        # Auto-detect wallet if not provided
        if not wallet_file:
            wallet_file = self._auto_detect_wallet()
        
        # Load wallet
        with open(wallet_file, 'r') as f:
            wallet = orjson.loads(f.read())
        
        self.miner_address = wallet['address']
        self.wallet_name = Path(wallet_file).stem
        
        print(f"[Communicator] Loaded wallet: {self.wallet_name}")
        print(f"[Communicator] Miner address: {self.miner_address}")
        
        # Load private key for encryption
        private_key = None
        if enable_encryption and 'private_key' in wallet:
            try:
                private_key = SigningKey.from_string(
                    bytes.fromhex(wallet['private_key']),
                    curve=SECP256k1
                )
                print(f"[Communicator] Encryption: ENABLED (E2E using ECDH + AES-256)")
            except Exception as e:
                print(f"[Communicator] Warning: Could not load private key: {e}")
                print(f"[Communicator] Encryption: DISABLED")
        else:
            print(f"[Communicator] Encryption: DISABLED (enable_encryption={enable_encryption})")
        
        # Connect to tunnel server
        self.client = TunnelTransferClient(
            self.miner_address,
            TUNNEL_SERVER,
            TUNNEL_PORT,
            private_key=private_key,
            enable_encryption=enable_encryption
        )
        
        # Message queue
        self.messages = []
        self.running = False
    
    def _auto_detect_wallet(self) -> str:
        """Auto-detect wallet file"""
        wallet_dir = Path(__file__).parent / "wallets"
        wallets = list(wallet_dir.glob("*.json"))
        
        if not wallets:
            print("[ERROR] No wallet files found in user/wallets/")
            print("Please create a wallet first: python user/CreateWallet.py")
            sys.exit(1)
        
        if len(wallets) == 1:
            return str(wallets[0])
        
        # Let user choose
        print("\n[Wallet Selection]")
        print("Multiple wallets found:")
        for i, wallet in enumerate(wallets, 1):
            with open(wallet) as f:
                w = orjson.loads(f.read())
            print(f"  {i}. {wallet.stem} - {w['address']}")
        
        choice = int(input("\nSelect wallet (1-{}): ".format(len(wallets))))
        return str(wallets[choice - 1])
    
    def connect(self) -> bool:
        """Connect to tunnel server"""
        print(f"\n[Connecting] Tunnel server: {TUNNEL_SERVER}:{TUNNEL_PORT}")
        
        if self.client.register():
            print("[Connected] Successfully registered with tunnel server")
            
            # Start listening thread
            self.running = True
            listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
            listen_thread.start()
            
            return True
        else:
            print("[ERROR] Failed to connect to tunnel server")
            return False
    
    def _listen_loop(self):
        """Background listener for incoming messages"""
        while self.running:
            try:
                data, addr = self.client.sock.recvfrom(65536)  # 64KB buffer for files
                packet = orjson.loads(data.decode('utf-8'))
                
                if packet.get('type') == 'MESSAGE_RECEIVED':
                    self._handle_message(packet)
                    
            except Exception as e:
                if self.running:
                    pass  # Ignore timeout errors
    
    def _handle_message(self, packet: dict):
        """Handle incoming message or file"""
        sender = packet.get('sender')
        message = packet.get('message')
        timestamp = packet.get('timestamp')
        
        # Check if it's a file transfer
        if message.startswith("FILE:"):
            self._handle_file_transfer(sender, message)
        else:
            # Regular text message
            time_str = time.strftime("%H:%M:%S", time.localtime(timestamp))
            print(f"\n[{time_str}] {sender[:10]}...: {message}")
            print(">>> ", end="", flush=True)  # Re-show prompt
    
    def _handle_file_transfer(self, sender: str, message: str):
        """Handle incoming file"""
        try:
            # Parse: FILE:filename:base64data
            parts = message.split(":", 2)
            filename = parts[1]
            file_data = base64.b64decode(parts[2])
            
            # Save to received_files directory
            received_dir = Path(__file__).parent / "received_files"
            received_dir.mkdir(exist_ok=True)
            
            filepath = received_dir / filename
            with open(filepath, 'wb') as f:
                f.write(file_data)
            
            print(f"\n[File Received] {filename} ({len(file_data)} bytes) from {sender[:10]}...")
            print(f"[Saved] {filepath}")
            print(">>> ", end="", flush=True)
            
        except Exception as e:
            print(f"\n[ERROR] Failed to receive file: {e}")
    
    def list_online_miners(self) -> list:
        """Get list of online miners"""
        print("\n[Scanning] Checking for online miners...")
        
        # Get all wallet files (potential miners)
        wallet_dir = Path(__file__).parent / "wallets"
        wallets = list(wallet_dir.glob("*.json"))
        
        online_miners = []
        
        for wallet_file in wallets:
            with open(wallet_file) as f:
                wallet = orjson.loads(f.read())
            
            address = wallet['address']
            
            # Skip self
            if address == self.miner_address:
                continue
            
            # Check status
            status = self.client.check_miner_status(address)
            
            if status.get('status') == 'online':
                online_miners.append({
                    'address': address,
                    'wallet': wallet_file.stem,
                    'last_seen': status.get('last_seen', 0)
                })
        
        return online_miners
    
    def send_message(self, recipient: str, message: str) -> bool:
        """Send text message to another miner"""
        return self.client.send_message(recipient, message)
    
    def send_file(self, recipient: str, filepath: str) -> bool:
        """Send file to another miner"""
        try:
            file_path = Path(filepath)
            
            if not file_path.exists():
                print(f"[ERROR] File not found: {filepath}")
                return False
            
            # Read file and encode
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # Check size (max 60KB for UDP)
            if len(file_data) > 60000:
                print(f"[ERROR] File too large ({len(file_data)} bytes). Max 60KB")
                return False
            
            # Encode and send
            encoded = base64.b64encode(file_data).decode('utf-8')
            message = f"FILE:{file_path.name}:{encoded}"
            
            print(f"[Sending] {file_path.name} ({len(file_data)} bytes)...")
            result = self.client.send_message(recipient, message)
            
            if result:
                print(f"[Sent] File sent successfully")
            
            return result
            
        except Exception as e:
            print(f"[ERROR] Failed to send file: {e}")
            return False
    
    def start_chat(self):
        """Start interactive chat interface"""
        print("\n" + "="*70)
        print("PHN MINER COMMUNICATION - CHAT INTERFACE")
        print("="*70)
        print(f"Your Address: {self.miner_address}")
        print("="*70)
        print("\nCommands:")
        print("  /list          - List online miners")
        print("  /send <addr>   - Send message to miner")
        print("  /file <addr> <path> - Send file to miner")
        print("  /quit          - Exit chat")
        print("="*70)
        
        current_recipient = None
        
        while True:
            try:
                if current_recipient:
                    prompt = f"[To: {current_recipient[:10]}...] >>> "
                else:
                    prompt = ">>> "
                
                user_input = input(prompt).strip()
                
                if not user_input:
                    continue
                
                # Commands
                if user_input.startswith("/"):
                    parts = user_input.split(maxsplit=2)
                    cmd = parts[0].lower()
                    
                    if cmd == "/quit":
                        print("\n[Goodbye] Closing connection...")
                        self.running = False
                        break
                    
                    elif cmd == "/list":
                        online = self.list_online_miners()
                        if online:
                            print(f"\n[Online Miners] {len(online)} found:")
                            for i, miner in enumerate(online, 1):
                                print(f"  {i}. {miner['wallet']}")
                                print(f"     Address: {miner['address']}")
                                print(f"     Last seen: {miner['last_seen']:.1f}s ago")
                        else:
                            print("\n[No Miners] No other miners online")
                    
                    elif cmd == "/send":
                        if len(parts) < 2:
                            print("[Usage] /send <address>")
                        else:
                            current_recipient = parts[1]
                            print(f"[Chat] Now chatting with {current_recipient[:10]}...")
                            print("[Tip] Type your message and press Enter to send")
                    
                    elif cmd == "/file":
                        if len(parts) < 3:
                            print("[Usage] /file <address> <filepath>")
                        else:
                            recipient = parts[1]
                            filepath = parts[2]
                            self.send_file(recipient, filepath)
                    
                    else:
                        print(f"[Unknown] Command not recognized: {cmd}")
                
                else:
                    # Send message to current recipient
                    if current_recipient:
                        if self.send_message(current_recipient, user_input):
                            time_str = time.strftime("%H:%M:%S")
                            print(f"[{time_str}] You: {user_input}")
                        else:
                            print("[ERROR] Failed to send message")
                            print("[Hint] Is the recipient online? Use /list to check")
                    else:
                        print("[ERROR] No recipient selected")
                        print("[Hint] Use /send <address> to select a recipient")
                
            except KeyboardInterrupt:
                print("\n\n[Goodbye] Closing connection...")
                self.running = False
                break
            except Exception as e:
                print(f"[ERROR] {e}")
        
        self.client.stop()


def main():
    """Main entry point"""
    print("="*70)
    print("PHN MINER COMMUNICATION")
    print("="*70)
    print("Auto-connecting to tunnel server...")
    print("="*70)
    
    try:
        # Create communicator (auto-detects wallet)
        comm = MinerCommunicator()
        
        # Connect to tunnel
        if not comm.connect():
            print("\n[ERROR] Cannot connect to tunnel server")
            print(f"[Hint] Make sure tunnel server is running:")
            print(f"       python user/TunnelServer.py")
            return
        
        # Start chat interface
        comm.start_chat()
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
