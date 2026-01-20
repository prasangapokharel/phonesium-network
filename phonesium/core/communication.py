"""
Phonesium Communication - Peer-to-peer communication for miners
Simple message relay system
"""

import socket
import orjson
import time
from typing import Optional, Dict

from .config import DEFAULT_TUNNEL_HOST, DEFAULT_TUNNEL_PORT
from .wallet import Wallet
from .exceptions import NetworkError


class TunnelClient:
    """
    Simple tunnel client for miner-to-miner communication

    Example:
        >>> from phonesium import Wallet, TunnelClient
        >>>
        >>> wallet = Wallet.create()
        >>> client = TunnelClient(wallet)
        >>>
        >>> # Register with tunnel server
        >>> client.register()
        >>>
        >>> # Send message to another miner
        >>> client.send_message("PHN...", "Hello from miner!")
        >>>
        >>> # Check if another miner is online
        >>> status = client.check_miner_status("PHN...")
    """

    def __init__(
        self, wallet: Wallet, tunnel_host: str = None, tunnel_port: int = None
    ):
        """
        Initialize tunnel client

        Args:
            wallet: Miner wallet
            tunnel_host: Tunnel server host (default from config)
            tunnel_port: Tunnel server port (default from config)
        """
        self.wallet = wallet
        self.tunnel_host = tunnel_host or DEFAULT_TUNNEL_HOST
        self.tunnel_port = tunnel_port or DEFAULT_TUNNEL_PORT

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("0.0.0.0", 0))
        self.sock.settimeout(5)

        self.registered = False

        print(f"[Tunnel] Client initialized for: {wallet.address[:10]}...")

    def register(self) -> bool:
        """
        Register with tunnel server

        Returns:
            bool: True if registration successful
        """
        packet = {
            "type": "REGISTER",
            "miner_address": self.wallet.address,
            "public_key": self.wallet.public_key,
            "timestamp": time.time(),
            "signature": "placeholder",
        }

        try:
            self.sock.sendto(
                orjson.dumps(packet).encode("utf-8"),
                (self.tunnel_host, self.tunnel_port),
            )

            data, _ = self.sock.recvfrom(4096)
            response = orjson.loads(data)

            if response.get("type") == "REGISTER_OK":
                self.registered = True
                print(f"[Tunnel] Registered successfully")
                return True
        except Exception as e:
            print(f"[Tunnel] Registration failed: {e}")

        return False

    def send_message(self, recipient: str, message: str) -> bool:
        """
        Send message to another miner

        Args:
            recipient: Recipient miner address
            message: Message to send

        Returns:
            bool: True if message sent successfully
        """
        if not self.registered:
            if not self.register():
                return False

        packet = {
            "type": "MESSAGE",
            "sender": self.wallet.address,
            "recipient": recipient,
            "message": message,
            "encrypted": False,
            "timestamp": time.time(),
        }

        try:
            self.sock.sendto(
                orjson.dumps(packet).encode("utf-8"),
                (self.tunnel_host, self.tunnel_port),
            )

            data, _ = self.sock.recvfrom(4096)
            response = orjson.loads(data)

            if response.get("type") == "MESSAGE_SENT":
                print(f"[Tunnel] Message sent to {recipient[:10]}...")
                return True
            elif response.get("type") == "ERROR":
                print(f"[Tunnel] Error: {response.get('message')}")
                return False
        except Exception as e:
            print(f"[Tunnel] Send failed: {e}")

        return False

    def check_miner_status(self, target_address: str) -> Dict:
        """
        Check if another miner is online

        Args:
            target_address: Miner address to check

        Returns:
            dict: Status information
        """
        packet = {
            "type": "LOOKUP",
            "target_address": target_address,
            "timestamp": time.time(),
        }

        try:
            self.sock.sendto(
                orjson.dumps(packet).encode("utf-8"),
                (self.tunnel_host, self.tunnel_port),
            )

            data, _ = self.sock.recvfrom(4096)
            response = orjson.loads(data)

            if response.get("type") == "LOOKUP_RESULT":
                return response
        except Exception as e:
            print(f"[Tunnel] Lookup failed: {e}")

        return {"status": "error"}

    def ping(self) -> bool:
        """
        Send keepalive ping to server

        Returns:
            bool: True if ping successful
        """
        packet = {
            "type": "PING",
            "miner_address": self.wallet.address,
            "timestamp": time.time(),
        }

        try:
            self.sock.sendto(
                orjson.dumps(packet).encode("utf-8"),
                (self.tunnel_host, self.tunnel_port),
            )
            return True
        except Exception as e:
            print(f"[Tunnel] Ping failed: {e}")
            return False

    def close(self):
        """Close the tunnel client"""
        self.sock.close()
        print(f"[Tunnel] Client closed")

    def __repr__(self) -> str:
        return f"TunnelClient(miner={self.wallet.address[:10]}..., registered={self.registered})"
