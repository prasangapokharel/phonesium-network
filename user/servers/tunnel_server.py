#!/usr/bin/env python3
"""
PHN Tunnel Transfer - Standalone Tunnel Server
Run this to start the UDP tunnel server for miner-to-miner communication
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.tunnel_transfer import TunnelTransferServer

def main():
    print("="*60)
    print("PHN BLOCKCHAIN - TUNNEL TRANSFER SERVER")
    print("="*60)
    print("UDP Server for direct miner-to-miner communication")
    print("Port: 9999")
    print("="*60)
    print("\nStarting server...\n")
    
    server = TunnelTransferServer(host="0.0.0.0", port=9999)
    
    try:
        server.start()
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        server.stop()
        print("Server stopped")

if __name__ == "__main__":
    main()
