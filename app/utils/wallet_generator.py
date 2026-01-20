# wallet_generator.py - Wallet generation utility for PHN blockchain
import orjson
import os
import sqlite3
from datetime import datetime
from app.core.transactions.base import generate_keypair
from app.core.config import settings

def init_wallet_db():
    """Initialize the wallet database"""
    os.makedirs("sqlite_data", exist_ok=True)
    db_path = "sqlite_data/wallets.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create wallets table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS wallets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            address_number INTEGER UNIQUE,
            address TEXT UNIQUE NOT NULL,
            private_key TEXT NOT NULL,
            public_key TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            label TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def get_next_address_number():
    """Get the next address number"""
    init_wallet_db()
    db_path = "sqlite_data/wallets.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT MAX(address_number) FROM wallets")
    result = cursor.fetchone()
    
    conn.close()
    
    return (result[0] or 0) + 1

def save_wallet_to_db(wallet, label=None):
    """Save wallet to SQLite database"""
    init_wallet_db()
    db_path = "sqlite_data/wallets.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    address_number = get_next_address_number()
    
    cursor.execute('''
        INSERT INTO wallets (address_number, address, private_key, public_key, label)
        VALUES (?, ?, ?, ?, ?)
    ''', (address_number, wallet['address'], wallet['private_key'], wallet['public_key'], label))
    
    conn.commit()
    conn.close()
    
    wallet['address_number'] = address_number
    return address_number

def get_wallet_by_address(address):
    """Get wallet from database by address"""
    init_wallet_db()
    db_path = "sqlite_data/wallets.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT address_number, address, private_key, public_key, created_at, label
        FROM wallets WHERE address = ?
    ''', (address,))
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {
            'address_number': result[0],
            'address': result[1],
            'private_key': result[2],
            'public_key': result[3],
            'created_at': result[4],
            'label': result[5]
        }
    return None

def get_wallet_by_number(address_number):
    """Get wallet from database by address number"""
    init_wallet_db()
    db_path = "sqlite_data/wallets.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT address_number, address, private_key, public_key, created_at, label
        FROM wallets WHERE address_number = ?
    ''', (address_number,))
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {
            'address_number': result[0],
            'address': result[1],
            'private_key': result[2],
            'public_key': result[3],
            'created_at': result[4],
            'label': result[5]
        }
    return None

def list_all_wallets():
    """List all wallets from database"""
    init_wallet_db()
    db_path = "sqlite_data/wallets.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT address_number, address, private_key, public_key, created_at, label
        FROM wallets ORDER BY address_number
    ''')
    
    results = cursor.fetchall()
    conn.close()
    
    wallets = []
    for result in results:
        wallets.append({
            'address_number': result[0],
            'address': result[1],
            'private_key': result[2],
            'public_key': result[3],
            'created_at': result[4],
            'label': result[5]
        })
    
    return wallets

def get_wallet_count():
    """Get total number of wallets"""
    init_wallet_db()
    db_path = "sqlite_data/wallets.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM wallets")
    result = cursor.fetchone()
    
    conn.close()
    
    return result[0]

def generate_new_wallet(label=None, save_to_db=True):
    """Generate a new wallet with private key, public key, and PHN address"""
    private_key, public_key, address = generate_keypair()
    
    wallet = {
        "private_key": private_key,
        "public_key": public_key,
        "address": address,
        "balance": 0.0
    }
    
    if save_to_db:
        address_number = save_wallet_to_db(wallet, label)
        wallet['address_number'] = address_number
        print(f"💾 Wallet saved to database with address number: {address_number}")
    
    return wallet

def save_wallet_to_file(wallet, filename=None):
    """Save wallet to a file"""
    if filename is None:
        address_num = wallet.get('address_number', 'unknown')
        filename = f"wallet_{address_num}_{wallet['address'][-8:]}.json"
    
    # Create wallets directory
    wallets_dir = "wallets"
    os.makedirs(wallets_dir, exist_ok=True)
    
    filepath = os.path.join(wallets_dir, filename)
    
    with open(filepath, "wb") as f:
        f.write(orjson.dumps(wallet, option=orjson.OPT_INDENT_2))
    
    print(f"📁 Wallet saved to file: {filepath}")
    return filepath

def generate_multiple_wallets(count=1, save_to_db=True):
    """Generate multiple wallets"""
    wallets = []
    
    for i in range(count):
        wallet = generate_new_wallet(save_to_db=save_to_db)
        wallets.append(wallet)
        address_num = wallet.get('address_number', 'N/A')
        print(f"Generated wallet {i+1}/{count}: #{address_num} - {wallet['address']}")
    
    return wallets

def display_wallet(wallet):
    """Display wallet information in a formatted way"""
    address_num = wallet.get('address_number', 'N/A')
    print("\n" + "="*60)
    print("PHN WALLET GENERATED")
    print("="*60)
    print(f"Address Number: #{address_num}")
    print(f"Address:        {wallet['address']}")
    print(f"Private Key:    {wallet['private_key']}")
    print(f"Public Key:     {wallet['public_key']}")
    print(f"Balance:        {wallet['balance']} PHN")
    if wallet.get('label'):
        print(f"Label:          {wallet['label']}")
    print("="*60)
    print("⚠️  IMPORTANT: Keep your private key safe and secret!")
    print("⚠️  Anyone with your private key can access your funds!")
    print("="*60)

if __name__ == "__main__":
    # Generate a single wallet
    print("Generating new PHN wallet...")
    wallet = generate_new_wallet()
    display_wallet(wallet)
    
    # Save to file
    save_wallet_to_file(wallet)
    
    print(f"\nWallet saved to database and file")
