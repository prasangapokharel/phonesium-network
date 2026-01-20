#!/usr/bin/env python3
"""
PHN Network - Wallet Generator with AUTOMATIC ENCRYPTION
Generate new PHN wallets with private keys automatically encrypted
SECURITY: All wallets are encrypted by default using AES-256-GCM
"""

import sys
import os
import hashlib
import orjson
import getpass
from ecdsa import SigningKey, SECP256k1

# Add app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.utils.secure_wallet import SecureWalletStorage

def generate_keypair():
    """Generate new private key, public key, and PHN address"""
    # Generate private key
    sk = SigningKey.generate(curve=SECP256k1)
    private_key = sk.to_string().hex()
    
    # Get public key
    vk = sk.get_verifying_key()
    public_key = vk.to_string().hex()
    
    # Generate PHN address
    public_key_bytes = bytes.fromhex(public_key)
    address_hash = hashlib.sha256(public_key_bytes).hexdigest()[:40]
    address = f"PHN{address_hash}"
    
    return private_key, public_key, address

def save_wallet_to_file(wallet, password=None, filename=None):
    """
    Save wallet to JSON file with AUTOMATIC ENCRYPTION
    SECURITY: Private key is encrypted by default
    """
    if filename is None:
        filename = f"wallet_{wallet['address'][-8:]}.json"
    
    os.makedirs("wallets", exist_ok=True)
    filepath = os.path.join("wallets", filename)
    
    # Encrypt wallet if password provided
    if password:
        print("\n[SECURITY] Encrypting wallet with AES-256-GCM...")
        encrypted_data = SecureWalletStorage.encrypt_wallet(wallet, password)
        
        # Save encrypted wallet
        with open(filepath, 'w') as f:
            f.write(orjson.dumps(encrypted_data, option=orjson.OPT_INDENT_2))
        
        print("[SECURITY] Wallet encrypted successfully!")
        print("[SECURITY] Password required to access private key")
    else:
        # Save unencrypted (NOT RECOMMENDED - show warning)
        print("\n[WARNING] Saving wallet WITHOUT encryption!")
        print("[WARNING] Private key will be stored in PLAIN TEXT")
        print("[WARNING] This is NOT SECURE - anyone with file access can steal funds")
        
        with open(filepath, 'w') as f:
            f.write(orjson.dumps(wallet, option=orjson.OPT_INDENT_2))
    
    return filepath

def display_wallet(wallet, encrypted=False):
    """Display wallet information"""
    print("\n" + "="*60)
    print("PHN WALLET GENERATED")
    print("="*60)
    print(f"Address:     {wallet['address']}")
    
    if encrypted:
        print(f"Private Key: [ENCRYPTED - Password Required]")
        print(f"Public Key:  {wallet['public_key']}")
        print("="*60)
        print("[SECURITY] Private key is encrypted with AES-256-GCM")
        print("[SECURITY] You need your password to access the private key")
    else:
        print(f"Private Key: {wallet['private_key']}")
        print(f"Public Key:  {wallet['public_key']}")
        print("="*60)
        print("[WARNING] Wallet saved WITHOUT encryption!")
    
    print("="*60)
    print("KEEP YOUR PRIVATE KEY & PASSWORD SAFE!")
    print("Anyone with access can steal your funds!")
    print("="*60)

def generate_wallet(save_to_file=True, password=None):
    """
    Generate a new PHN wallet with AUTOMATIC ENCRYPTION
    SECURITY: Strongly recommends password for encryption
    """
    private_key, public_key, address = generate_keypair()
    
    wallet = {
        "address": address,
        "private_key": private_key,
        "public_key": public_key,
        "created_at": None
    }
    
    if save_to_file:
        filepath = save_wallet_to_file(wallet, password)
        print(f"\n[INFO] Wallet saved to: {filepath}")
    
    return wallet

def generate_multiple_wallets(count, password=None):
    """Generate multiple wallets with encryption"""
    wallets = []
    
    for i in range(count):
        wallet = generate_wallet(save_to_file=True, password=password)
        wallets.append(wallet)
        print(f"[INFO] Generated wallet {i+1}/{count}: {wallet['address']}")
    
    return wallets

def main():
    """Main wallet generator interface with AUTOMATIC ENCRYPTION"""
    print("="*60)
    print("PHN Network - Secure Wallet Generator")
    print("="*60)
    print("SECURITY: All wallets are encrypted by default")
    print("="*60)
    
    try:
        count_input = input("\nHow many wallets to generate? (default: 1): ").strip()
        count = int(count_input) if count_input else 1
        
        if count < 1:
            print("[ERROR] Count must be at least 1")
            return
        
        # Ask for encryption password (STRONGLY RECOMMENDED)
        print("\n[SECURITY] Wallet encryption setup")
        print("[SECURITY] Without a password, private keys are stored in PLAIN TEXT")
        encrypt_choice = input("\nEncrypt wallet with password? (YES/no): ").strip().lower()
        
        password = None
        encrypted = False
        
        if encrypt_choice in ['', 'y', 'yes']:
            password = getpass.getpass("Enter encryption password: ")
            password_confirm = getpass.getpass("Confirm password: ")
            
            if password != password_confirm:
                print("\n[ERROR] Passwords do not match!")
                return
            
            if len(password) < 8:
                print("\n[WARNING] Password is short (less than 8 characters)")
                proceed = input("Continue anyway? (yes/no): ").strip().lower()
                if proceed not in ['y', 'yes']:
                    return
            
            encrypted = True
            print("\n[SECURITY] Wallet will be encrypted with AES-256-GCM")
        else:
            print("\n[WARNING] Wallet will NOT be encrypted!")
            print("[WARNING] This is DANGEROUS - private keys will be in PLAIN TEXT")
            confirm = input("Are you SURE you want to continue without encryption? (yes/no): ").strip().lower()
            if confirm not in ['yes']:
                print("\n[INFO] Wallet generation cancelled. Please encrypt your wallet for security.")
                return
        
        print(f"\n[INFO] Generating {count} wallet(s)...")
        
        if count == 1:
            wallet = generate_wallet(password=password)
            display_wallet(wallet, encrypted=encrypted)
        else:
            wallets = generate_multiple_wallets(count, password=password)
            print(f"\n[SUCCESS] Generated {len(wallets)} wallets successfully!")
            if encrypted:
                print("[SECURITY] All wallets encrypted with the same password")
        
    except KeyboardInterrupt:
        print("\n\n[INFO] Operation cancelled.")
    except ValueError:
        print("\n[ERROR] Invalid input. Please enter a valid number.")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
