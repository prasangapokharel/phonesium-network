#!/usr/bin/env python3
"""
PHN Network - Balance Checker
Check PHN token balance for any address
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

NODE_URL = os.getenv("NODE_URL", "http://localhost:8765")

def get_balance(address):
    """Get balance for an address"""
    try:
        response = requests.post(f"{NODE_URL}/get_balance", 
                               json={"address": address}, 
                               timeout=10)
        if response.status_code == 200:
            data = response.json()
            return float(data.get("balance", 0))
        else:
            print(f"Error: {response.text}")
            return None
    except Exception as e:
        print(f"Network error: {e}")
        return None

def validate_address(address):
    """Validate PHN address format"""
    if not address:
        return False
    if not address.startswith("PHN"):
        return False
    if len(address) != 43:
        return False
    return True

def main():
    """Main balance checker interface"""
    print("PHN Network - Balance Checker")
    print("=" * 40)
    print(f"Connected to: {NODE_URL}")
    print("=" * 40)
    
    try:
        while True:
            address = input("\nEnter PHN address (or 'quit' to exit): ").strip()
            
            if address.lower() == 'quit':
                break
            
            if not validate_address(address):
                print("Invalid address format. Must start with 'PHN' and be 43 characters long.")
                continue
            
            print(f"Checking balance for: {address}")
            balance = get_balance(address)
            
            if balance is not None:
                print(f"Balance: {balance:.6f} PHN")
            else:
                print("Failed to get balance")
                
    except KeyboardInterrupt:
        print("\nOperation cancelled")

if __name__ == "__main__":
    main()
