#!/usr/bin/env python3
"""
PHN Network - Send Tokens
Send PHN tokens to another address
"""

import orjson
import time
import hashlib
import requests
import sys
import random
from dotenv import load_dotenv
from ecdsa import SigningKey, SECP256k1
import os

load_dotenv()

NODE_URL = os.getenv("NODE_URL", "http://localhost:8765")
if not NODE_URL:
    print("[ERROR] NODE_URL not set in .env file")
    print("[ERROR] Please set NODE_URL=http://localhost:8765 in .env")
    sys.exit(1)


def get_public_key_from_private_key(private_key_hex):
    """Get public key from private key"""
    sk = SigningKey.from_string(bytes.fromhex(private_key_hex), curve=SECP256k1)
    vk = sk.get_verifying_key()
    return vk.to_string().hex()


def generate_address_from_public_key(public_key_hex):
    """Generate PHN address from public key"""
    public_key_bytes = bytes.fromhex(public_key_hex)
    address_hash = hashlib.sha256(public_key_bytes).hexdigest()[:40]
    return f"PHN{address_hash}"


def get_mining_info():
    """Get minimum fee from node"""
    try:
        response = requests.get(f"{NODE_URL}/mining_info", timeout=10)
        if response.status_code == 200:
            return response.json()
        return {"min_tx_fee": 0.02}
    except:
        return {"min_tx_fee": 0.02}


def get_balance(address):
    """Get balance for an address"""
    try:
        response = requests.post(
            f"{NODE_URL}/get_balance", json={"address": address}, timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            return float(data.get("balance", 0))
        return 0.0
    except:
        return 0.0


def create_transaction(private_key, recipient, amount, fee):
    """Create and sign a transaction with nonce"""
    # Generate sender info
    public_key = get_public_key_from_private_key(private_key)
    sender_address = generate_address_from_public_key(public_key)

    # Create transaction with nonce
    timestamp = time.time()
    nonce = random.randint(0, 999999)  # SECURITY: Add nonce to prevent TXID collision

    tx = {
        "sender": public_key,
        "recipient": recipient,
        "amount": amount,
        "fee": fee,
        "timestamp": timestamp,
        "nonce": nonce,
        "signature": "",
    }

    # Generate TXID with nonce
    hash_input = f"{tx['sender']}{tx['recipient']}{tx['amount']}{tx['fee']}{tx['timestamp']}{tx['nonce']}"
    tx["txid"] = hashlib.sha256(hash_input.encode()).hexdigest()

    # Sign transaction
    sk = SigningKey.from_string(bytes.fromhex(private_key), curve=SECP256k1)
    tx_copy = dict(tx)
    tx_copy.pop("signature", None)
    tx_json = orjson.dumps(tx_copy, option=orjson.OPT_SORT_KEYS)
    tx["signature"] = sk.sign(tx_json).hex()

    return tx, sender_address


def submit_transaction(tx):
    """Submit transaction to node"""
    try:
        response = requests.post(f"{NODE_URL}/send_tx", json={"tx": tx}, timeout=10)
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            error_data = (
                response.json()
                if "application/json" in response.headers.get("content-type", "")
                else {"error": response.text}
            )
            return {"success": False, "error": error_data.get("error", "Unknown error")}
    except Exception as e:
        return {"success": False, "error": str(e)}


def validate_private_key(private_key):
    """Validate private key format"""
    try:
        if len(private_key) != 64:
            return False
        bytes.fromhex(private_key)
        return True
    except:
        return False


def validate_address(address):
    """Validate PHN address format"""
    return address.startswith("PHN") and len(address) == 43


def main():
    """Main send tokens interface"""
    print("PHN Network - Send Tokens")
    print("=" * 40)
    print(f"Connected to: {NODE_URL}")

    # Get current minimum fee
    mining_info = get_mining_info()
    min_fee = mining_info.get("min_tx_fee", 0.02)
    print(f"Minimum fee: {min_fee} PHN")
    print("=" * 40)

    try:
        # Get private key
        while True:
            private_key = input("Enter your private key (64 hex chars): ").strip()
            if validate_private_key(private_key):
                break
            print("Invalid private key format")

        # Get recipient address
        while True:
            recipient = input("Enter recipient address (PHN...): ").strip()
            if validate_address(recipient):
                break
            print("Invalid address format")

        # Get amount
        while True:
            try:
                amount = float(input("Enter amount to send: ").strip())
                if amount > 0:
                    break
                print("Amount must be greater than 0")
            except ValueError:
                print("Invalid amount")

        # Get fee
        fee_input = input(f"Enter fee (default {min_fee}): ").strip()
        try:
            fee = float(fee_input) if fee_input else min_fee
            if fee < min_fee:
                print(f"Fee too low, using minimum: {min_fee}")
                fee = min_fee
        except ValueError:
            fee = min_fee

        # Create transaction
        print("\nCreating transaction...")
        tx, sender_address = create_transaction(private_key, recipient, amount, fee)

        # Check balance
        sender_balance = max(get_balance(sender_address), get_balance(tx["sender"]))
        total_needed = amount + fee

        print(f"\nTransaction Summary:")
        print(f"From:   {sender_address}")
        print(f"To:     {recipient}")
        print(f"Amount: {amount} PHN")
        print(f"Fee:    {fee} PHN")
        print(f"Total:  {total_needed} PHN")
        print(f"Balance: {sender_balance} PHN")

        if sender_balance < total_needed:
            print(f"Insufficient balance! Need {total_needed}, have {sender_balance}")
            return

        # Confirm
        confirm = input("\nConfirm transaction? (y/N): ").strip().lower()
        if confirm != "y":
            print("Transaction cancelled")
            return

        # Submit transaction
        print("Submitting transaction...")
        result = submit_transaction(tx)

        if result["success"]:
            print("Transaction submitted successfully!")
            print(f"Transaction ID: {tx['txid']}")
        else:
            print(f"Transaction failed: {result['error']}")

    except KeyboardInterrupt:
        print("\nOperation cancelled")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
