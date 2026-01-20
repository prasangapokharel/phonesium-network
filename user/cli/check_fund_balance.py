#!/usr/bin/env python3
"""
Check FUND address balance using Phonesium Client
"""

import sys
sys.path.insert(0, '.')

from phonesium.core.client import PhonesiumClient
from datetime import datetime

# FUND address
FUND_ADDRESS = "PHN0a2e1f46a128caa0fded990ac8f7c9fb5e7da8a6"

def main():
    print("=" * 70)
    print("PHN BLOCKCHAIN - FUND ADDRESS BALANCE CHECK")
    print("Using Phonesium Client")
    print("=" * 70)
    print()
    
    # Connect to node
    print(f"Connecting to node: http://localhost:8765")
    client = PhonesiumClient("http://localhost:8765")
    
    # Get FUND balance
    print(f"Querying balance for FUND address...")
    print(f"Address: {FUND_ADDRESS}")
    print()
    
    try:
        balance = client.get_balance(FUND_ADDRESS)
        
        print("=" * 70)
        print(f"FUND ADDRESS BALANCE: {balance:.2f} PHN")
        print("=" * 70)
        print()
        
        # Get blockchain info manually
        print("Additional Information:")
        try:
            import requests
            response = requests.post("http://localhost:8765/get_blockchain", timeout=5)
            if response.status_code == 200:
                blockchain_data = response.json()
                height = blockchain_data.get("length", 0)
                print(f"  - Blockchain Height: {height} blocks")
                print(f"  - Total Supply: {height * 50} PHN")
                if height > 0:
                    print(f"  - FUND has: {(balance / (height * 50) * 100):.2f}% of total supply")
        except:
            pass
        print()
        
        # Check pending transactions
        try:
            import requests
            response = requests.post("http://localhost:8765/get_pending", timeout=5)
            if response.status_code == 200:
                pending_data = response.json()
                pending_count = pending_data.get("count", 0)
                print(f"  - Pending Transactions: {pending_count}")
                
                if pending_count > 0:
                    print()
                    print("Pending transactions will affect balance once mined:")
                    for tx in pending_data.get("pending_transactions", [])[:5]:
                        sender = tx.get("sender", "")
                        recipient = tx.get("recipient", "")
                        amount = tx.get("amount", 0)
                        
                        # Check if FUND is involved
                        if recipient == FUND_ADDRESS:
                            print(f"    -> FUND will RECEIVE {amount} PHN")
                        elif len(sender) == 128:  # Public key format
                            # Need to convert to address to check
                            pass
        except:
            pass
        
        print()
        print(f"Query completed at: {datetime.now().strftime('%H:%M:%S')}")
        
    except Exception as e:
        print(f"ERROR: Failed to get balance - {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
