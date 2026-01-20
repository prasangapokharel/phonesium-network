#!/usr/bin/env python3
"""Test what the miner sees for pending transactions"""

import requests

NODE_URL = "http://localhost:8765"

print("Fetching pending transactions as miner would...")
response = requests.post(f"{NODE_URL}/get_pending", timeout=10)
print(f"Status: {response.status_code}")
data = response.json()

print(f"\nPending transactions count: {data.get('count', 0)}")
print(f"Pending transactions array length: {len(data.get('pending_transactions', []))}")

print("\nPending transactions:")
for i, tx in enumerate(data.get('pending_transactions', []), 1):
    print(f"{i}. {tx['sender'][:20]}... -> {tx['recipient'][:20]}... | {tx['amount']} PHN (fee: {tx['fee']})")
