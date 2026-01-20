#!/usr/bin/env python3
"""
PHN Network - Blockchain Explorer
Browse blockchain data with complete transaction details
"""

import requests
import orjson
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

NODE_URL = os.getenv("NODE_URL", "http://localhost:8765")

class BlockchainExplorer:
    def __init__(self):
        self.blockchain = []
        self.blockchain_length = 0
        self.total_transactions = 0
        self.total_addresses = set()
        
    def fetch_blockchain_data(self):
        """Fetch complete blockchain data from node"""
        try:
            print("[FETCH] Fetching blockchain data from node...")
            response = requests.post(f"{NODE_URL}/get_blockchain", timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                self.blockchain = data.get("blockchain", [])
                self.blockchain_length = len(self.blockchain)
                self.analyze_blockchain()
                print(f"[OK] Loaded {self.blockchain_length} blocks with {self.total_transactions} transactions")
                return True
            else:
                print(f"[ERROR] Error fetching blockchain: {response.text}")
                return False
                
        except Exception as e:
            print(f"[ERROR] Network error: {str(e)}")
            return False
    
    def analyze_blockchain(self):
        """Analyze blockchain for statistics"""
        self.total_transactions = 0
        self.total_addresses = set()
        
        for block in self.blockchain:
            transactions = block.get("transactions", [])
            self.total_transactions += len(transactions)
            
            for tx in transactions:
                sender = tx.get("sender", "")
                recipient = tx.get("recipient", "")
                
                if sender and sender not in ["coinbase", "miners_pool"]:
                    self.total_addresses.add(sender)
                if recipient:
                    self.total_addresses.add(recipient)
    
    def format_timestamp(self, timestamp):
        """Format timestamp to readable date"""
        try:
            if isinstance(timestamp, (int, float)):
                return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
            return str(timestamp)
        except:
            return "Invalid timestamp"
    
    def format_address(self, address, length=20):
        """Format address for display"""
        if not address:
            return "N/A"
        if len(address) > length:
            return f"{address[:length]}..."
        return address
    
    def get_transaction_type(self, tx):
        """Determine transaction type"""
        sender = tx.get("sender", "")
        if sender == "coinbase":
            return "COINBASE", "[REWARD]"
        elif sender == "miners_pool":
            return "FEE_PAYOUT", "💸"
        else:
            return "TRANSFER", "💳"
    
    def display_blockchain_overview(self):
        """Display complete blockchain overview"""
        print("\n" + "=" * 80)
        print("📊 BLOCKCHAIN OVERVIEW")
        print("=" * 80)
        print(f"Total Blocks:        {self.blockchain_length}")
        print(f"Total Transactions:  {self.total_transactions}")
        print(f"Unique Addresses:    {len(self.total_addresses)}")
        
        if self.blockchain:
            latest_block = self.blockchain[-1]
            print(f"Latest Block Hash:   {latest_block.get('hash', 'N/A')}")
            print(f"Latest Block Time:   {self.format_timestamp(latest_block.get('timestamp'))}")
        
        print("=" * 80)
    
    def display_block_details(self, block_index):
        """Display detailed block information"""
        if block_index < 0 or block_index >= len(self.blockchain):
            print(f"[ERROR] Block #{block_index} not found")
            return
        
        block = self.blockchain[block_index]
        transactions = block.get("transactions", [])
        
        print(f"\n" + "=" * 80)
        print(f"📦 BLOCK #{block_index} DETAILS")
        print("=" * 80)
        print(f"Block Index:     {block.get('index', 'N/A')}")
        print(f"Block Hash:      {block.get('hash', 'N/A')}")
        print(f"Previous Hash:   {block.get('prev_hash', 'N/A')}")
        print(f"Timestamp:       {self.format_timestamp(block.get('timestamp'))}")
        print(f"Nonce:           {block.get('nonce', 'N/A')}")
        print(f"Transactions:    {len(transactions)}")
        
        # Calculate block statistics
        total_value = 0.0
        total_fees = 0.0
        coinbase_reward = 0.0
        
        for tx in transactions:
            amount = float(tx.get("amount", 0))
            fee = float(tx.get("fee", 0))
            
            if tx.get("sender") == "coinbase":
                coinbase_reward += amount
            elif tx.get("sender") != "miners_pool":
                total_value += amount
                total_fees += fee
        
        print(f"Coinbase Reward: {coinbase_reward:.6f} PHN")
        print(f"Total Value:     {total_value:.6f} PHN")
        print(f"Total Fees:      {total_fees:.6f} PHN")
        print("=" * 80)
        
        # Display all transactions in this block
        self.display_block_transactions(block_index)
    
    def convert_public_key_to_phn(self, address):
        """Convert public key to PHN address if it's a public key format"""
        if not address or address in ["coinbase", "miners_pool"]:
            return address
        
        # Check if it's a public key (128 hex characters)
        if len(address) == 128 and all(c in '0123456789abcdef' for c in address.lower()):
            try:
                import hashlib
                public_key_bytes = bytes.fromhex(address)
                address_hash = hashlib.sha256(public_key_bytes).hexdigest()[:40]
                return f"PHN{address_hash}"
            except:
                return address
        
        return address

    def format_address_with_conversion(self, address, length=40):
        """Format address and show PHN conversion if it's a public key"""
        if not address:
            return "N/A"
        
        # Convert public key to PHN address if needed
        phn_address = self.convert_public_key_to_phn(address)
        
        if phn_address != address:  # It was converted
            if len(phn_address) > length:
                return f"{phn_address[:length]}... (from pubkey)"
            return f"{phn_address} (from pubkey)"
        else:
            if len(address) > length:
                return f"{address[:length]}..."
            return address
    
    def display_block_transactions(self, block_index):
        """Display all transactions in a block"""
        if block_index < 0 or block_index >= len(self.blockchain):
            return
        
        block = self.blockchain[block_index]
        transactions = block.get("transactions", [])
        
        if not transactions:
            print("No transactions in this block")
            return
        
        print(f"\n💳 TRANSACTIONS IN BLOCK #{block_index}")
        print("-" * 80)
        
        for i, tx in enumerate(transactions, 1):
            tx_type, icon = self.get_transaction_type(tx)
            sender = tx.get('sender', 'N/A')
            recipient = tx.get('recipient', 'N/A')
            
            print(f"\n{icon} Transaction #{i} - {tx_type}")
            print(f"   TXID:        {tx.get('txid', 'N/A')}")
            print(f"   From:        {self.format_address_with_conversion(sender, 40)}")
            print(f"   To:          {self.format_address_with_conversion(recipient, 40)}")
            print(f"   Amount:      {float(tx.get('amount', 0)):.6f} PHN")
            print(f"   Fee:         {float(tx.get('fee', 0)):.6f} PHN")
            print(f"   Timestamp:   {self.format_timestamp(tx.get('timestamp'))}")
            print(f"   Signature:   {self.format_address(tx.get('signature', 'N/A'), 20)}")
    
    def display_transaction_details(self, txid):
        """Display detailed transaction information"""
        print(f"\n🔍 SEARCHING FOR TRANSACTION: {txid}")
        print("-" * 80)
        
        found = False
        for block_index, block in enumerate(self.blockchain):
            for tx_index, tx in enumerate(block.get("transactions", [])):
                if tx.get("txid") == txid:
                    found = True
                    tx_type, icon = self.get_transaction_type(tx)
                    sender = tx.get('sender', 'N/A')
                    recipient = tx.get('recipient', 'N/A')
                    
                    print(f"\n{icon} TRANSACTION FOUND")
                    print("=" * 80)
                    print(f"Transaction ID:  {tx.get('txid', 'N/A')}")
                    print(f"Block Height:    #{block_index}")
                    print(f"Block Hash:      {block.get('hash', 'N/A')}")
                    print(f"TX Index:        {tx_index}")
                    print(f"Type:            {tx_type}")
                    
                    # Show both raw and converted addresses
                    if sender != "coinbase" and sender != "miners_pool" and len(sender) == 128:
                        phn_sender = self.convert_public_key_to_phn(sender)
                        print(f"From (PHN):      {phn_sender}")
                        print(f"From (Raw):      {sender}")
                    else:
                        print(f"From:            {sender}")
                    
                    print(f"To:              {recipient}")
                    print(f"Amount:          {float(tx.get('amount', 0)):.6f} PHN")
                    print(f"Fee:             {float(tx.get('fee', 0)):.6f} PHN")
                    print(f"Timestamp:       {self.format_timestamp(tx.get('timestamp'))}")
                    print(f"Signature:       {tx.get('signature', 'N/A')}")
                    print(f"Block Time:      {self.format_timestamp(block.get('timestamp'))}")
                    print("=" * 80)
                    break
            if found:
                break
        
        if not found:
            print("[ERROR] Transaction not found in blockchain")
    
    def display_address_transactions(self, address):
        """Display all transactions for a specific address"""
        print(f"\n🏠 ADDRESS TRANSACTION HISTORY")
        print(f"Address: {address}")
        print("=" * 80)
        
        transactions_found = []
        balance = 0.0
        
        for block_index, block in enumerate(self.blockchain):
            for tx_index, tx in enumerate(block.get("transactions", [])):
                sender = tx.get("sender", "")
                recipient = tx.get("recipient", "")
                amount = float(tx.get("amount", 0))
                fee = float(tx.get("fee", 0))
                
                # Check if address is involved in this transaction
                if recipient == address:
                    balance += amount
                    transactions_found.append({
                        "type": "RECEIVED",
                        "block": block_index,
                        "tx_index": tx_index,
                        "amount": amount,
                        "fee": 0,
                        "counterpart": sender,
                        "txid": tx.get("txid", ""),
                        "timestamp": tx.get("timestamp"),
                        "block_hash": block.get("hash", "")
                    })
                
                if sender == address:
                    balance -= (amount + fee)
                    transactions_found.append({
                        "type": "SENT",
                        "block": block_index,
                        "tx_index": tx_index,
                        "amount": amount,
                        "fee": fee,
                        "counterpart": recipient,
                        "txid": tx.get("txid", ""),
                        "timestamp": tx.get("timestamp"),
                        "block_hash": block.get("hash", "")
                    })
        
        if not transactions_found:
            print("[ERROR] No transactions found for this address")
            return
        
        print(f"📊 SUMMARY")
        print(f"Total Transactions: {len(transactions_found)}")
        print(f"Final Balance:      {balance:.6f} PHN")
        print("\n📋 TRANSACTION LIST")
        print("-" * 80)
        
        for i, tx in enumerate(transactions_found, 1):
            icon = "📥" if tx["type"] == "RECEIVED" else "📤"
            sign = "+" if tx["type"] == "RECEIVED" else "-"
            
            print(f"\n{icon} Transaction #{i} - {tx['type']}")
            print(f"   Block Height:  #{tx['block']}")
            print(f"   Block Hash:    {self.format_address(tx['block_hash'], 20)}")
            print(f"   TXID:          {self.format_address(tx['txid'], 20)}")
            print(f"   Amount:        {sign}{tx['amount']:.6f} PHN")
            if tx['fee'] > 0:
                print(f"   Fee:           -{tx['fee']:.6f} PHN")
            print(f"   Counterpart:   {self.format_address(tx['counterpart'], 40)}")
            print(f"   Timestamp:     {self.format_timestamp(tx['timestamp'])}")
    
    def search_blocks_by_range(self, start_block, end_block):
        """Display blocks in a specific range"""
        if start_block < 0:
            start_block = 0
        if end_block >= len(self.blockchain):
            end_block = len(self.blockchain) - 1
        
        print(f"\n📦 BLOCKS {start_block} TO {end_block}")
        print("=" * 80)
        
        for i in range(start_block, end_block + 1):
            block = self.blockchain[i]
            tx_count = len(block.get("transactions", []))
            
            print(f"Block #{i:3d} | Hash: {self.format_address(block.get('hash', ''), 20)} | "
                  f"TXs: {tx_count:2d} | Time: {self.format_timestamp(block.get('timestamp'))}")
    
    def display_latest_transactions(self, count=10):
        """Display latest transactions across all blocks"""
        print(f"\n💳 LATEST {count} TRANSACTIONS")
        print("=" * 80)
        
        all_transactions = []
        
        # Collect all transactions with block info
        for block_index, block in enumerate(self.blockchain):
            for tx_index, tx in enumerate(block.get("transactions", [])):
                tx_with_block = dict(tx)
                tx_with_block["block_height"] = block_index
                tx_with_block["block_hash"] = block.get("hash", "")
                tx_with_block["tx_index"] = tx_index
                all_transactions.append(tx_with_block)
        
        # Sort by timestamp (latest first)
        all_transactions.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
        
        # Display latest transactions
        for i, tx in enumerate(all_transactions[:count], 1):
            tx_type, icon = self.get_transaction_type(tx)
            
            print(f"\n{icon} Transaction #{i} - {tx_type}")
            print(f"   Block Height:  #{tx['block_height']}")
            print(f"   TXID:          {self.format_address(tx.get('txid', ''), 20)}")
            print(f"   From:          {self.format_address_with_conversion(tx.get('sender', ''), 30)}")
            print(f"   To:            {self.format_address_with_conversion(tx.get('recipient', ''), 30)}")
            print(f"   Amount:        {float(tx.get('amount', 0)):.6f} PHN")
            print(f"   Fee:           {float(tx.get('fee', 0)):.6f} PHN")
            print(f"   Timestamp:     {self.format_timestamp(tx.get('timestamp'))}")
    
    def interactive_menu(self):
        """Interactive explorer menu"""
        while True:
            print("\n" + "=" * 60)
            print("🔍 PHN BLOCKCHAIN EXPLORER")
            print("=" * 60)
            print("1. 📊 Blockchain Overview")
            print("2. 📦 View Specific Block")
            print("3. 📋 View Block Range")
            print("4. 💳 Latest Transactions")
            print("5. 🔍 Search Transaction by TXID")
            print("6. 🏠 Search Address Transactions")
            print("7. 🔄 Refresh Blockchain Data")
            print("8. 🚪 Exit")
            print("-" * 60)
            
            try:
                choice = input("Select option (1-8): ").strip()
                
                if choice == "1":
                    self.display_blockchain_overview()
                
                elif choice == "2":
                    block_num = int(input(f"Enter block number (0-{self.blockchain_length-1}): "))
                    self.display_block_details(block_num)
                
                elif choice == "3":
                    start = int(input("Enter start block: "))
                    end = int(input("Enter end block: "))
                    self.search_blocks_by_range(start, end)
                
                elif choice == "4":
                    count = input("Number of transactions to show (default 10): ").strip()
                    count = int(count) if count else 10
                    self.display_latest_transactions(count)
                
                elif choice == "5":
                    txid = input("Enter transaction ID: ").strip()
                    self.display_transaction_details(txid)
                
                elif choice == "6":
                    address = input("Enter address: ").strip()
                    self.display_address_transactions(address)
                
                elif choice == "7":
                    self.fetch_blockchain_data()
                
                elif choice == "8":
                    print("👋 Goodbye!")
                    break
                
                else:
                    print("[ERROR] Invalid choice. Please select 1-8.")
                    
            except ValueError:
                print("[ERROR] Invalid input. Please enter a valid number.")
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"[ERROR] Error: {str(e)}")

def main():
    """Main explorer function"""
    print("🚀 Starting PHN Blockchain Explorer...")
    print(f"🌐 Connected to: {NODE_URL}")
    
    explorer = BlockchainExplorer()
    
    # Initial data fetch
    if not explorer.fetch_blockchain_data():
        print("[ERROR] Failed to connect to node. Please check NODE_URL in .env")
        return
    
    # Start interactive menu
    explorer.interactive_menu()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Explorer closed by user")
    except Exception as e:
        print(f"[ERROR] Unexpected error: {str(e)}")
