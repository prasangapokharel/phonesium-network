#!/usr/bin/env python3
"""
Check ALL wallet balances using Phonesium Client
Shows complete system state with 4 miners
"""

import sys
sys.path.insert(0, '.')

from phonesium.core.client import PhonesiumClient
from datetime import datetime
import requests

# All wallet addresses
WALLETS = {
    "FUND (Miner 3)": "PHN0a2e1f46a128caa0fded990ac8f7c9fb5e7da8a6",
    "MINER 1": "PHN718b7ad6d46933825778e5c95757e12b853e3d0c",
    "MINER 2": "PHN2d1395d421654092992c9994aee240e66b91458a",
    "MINER 4 (NEW)": "PHN814f3d1c55537d2f76e6632cb8251dd64f6d046d"
}

def main():
    print("=" * 80)
    print(" " * 20 + "PHN BLOCKCHAIN - COMPLETE SYSTEM STATUS")
    print(" " * 25 + "Using Phonesium Client Library")
    print("=" * 80)
    print()
    
    # Connect to node
    client = PhonesiumClient("http://localhost:8765")
    
    # Get blockchain info
    try:
        response = requests.post("http://localhost:8765/get_blockchain", timeout=5)
        blockchain_data = response.json()
        height = blockchain_data.get("length", 0)
        
        print(f"BLOCKCHAIN STATUS:")
        print(f"  Height: {height} blocks (0-{height-1})")
        print(f"  Total Supply: {height * 50} PHN")
        print()
    except:
        height = 0
        print("Could not fetch blockchain info")
    
    # Check all wallet balances
    print("WALLET BALANCES:")
    print("-" * 80)
    
    total_balance = 0
    balances = {}
    
    for name, address in WALLETS.items():
        try:
            balance = client.get_balance(address)
            balances[name] = balance
            total_balance += balance
            print(f"  {name:20s}: {balance:12.2f} PHN    [{address[:30]}...]")
        except Exception as e:
            print(f"  {name:20s}: ERROR - {e}")
    
    print("-" * 80)
    print(f"  {'TOTAL IN WALLETS':20s}: {total_balance:12.2f} PHN")
    print(f"  {'UNACCOUNTED':20s}: {(height * 50) - total_balance:12.2f} PHN (fees paid)")
    print()
    
    # Pending transactions
    try:
        response = requests.post("http://localhost:8765/get_pending", timeout=5)
        if response.status_code == 200:
            pending_data = response.json()
            pending_count = pending_data.get("count", 0)
            
            print(f"PENDING TRANSACTIONS: {pending_count}")
            
            if pending_count > 0:
                print("-" * 80)
                pending_to_fund = 0
                
                for i, tx in enumerate(pending_data.get("pending_transactions", []), 1):
                    recipient = tx.get("recipient", "")
                    amount = tx.get("amount", 0)
                    fee = tx.get("fee", 0)
                    
                    # Identify recipient
                    recipient_name = "Unknown"
                    for name, addr in WALLETS.items():
                        if addr == recipient:
                            recipient_name = name
                            break
                    
                    print(f"  TX {i}: {amount} PHN -> {recipient_name} (fee: {fee})")
                    
                    if recipient == WALLETS["FUND (Miner 3)"]:
                        pending_to_fund += amount
                
                if pending_to_fund > 0:
                    print()
                    print(f"  FUND will receive: +{pending_to_fund:.2f} PHN when transactions mine")
                    print(f"  FUND balance after mining: ~{balances['FUND (Miner 3)'] + pending_to_fund:.2f} PHN")
    except:
        pass
    
    print()
    print("=" * 80)
    
    # Mining status
    try:
        response = requests.get("http://localhost:8765/mining_info", timeout=5)
        if response.status_code == 200:
            mining_data = response.json()
            difficulty = mining_data.get("difficulty", 0)
            print(f"MINING INFO:")
            print(f"  Current Difficulty: {difficulty} (requires {16**difficulty:,} average hashes)")
            print(f"  Block Reward: {mining_data.get('block_reward', 0)} PHN")
            print(f"  Minimum Fee: {mining_data.get('min_tx_fee', 0)} PHN")
    except:
        pass
    
    print()
    print(f"Status checked at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

if __name__ == "__main__":
    main()
