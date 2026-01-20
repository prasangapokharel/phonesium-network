#!/usr/bin/env python3
"""
PHN Network - Secure Miner
Mines blocks and earns rewards. All parameters are dynamic from node.
SECURITY: Validates all node data to prevent cheating
"""

import time
import orjson
import hashlib
import random
import requests
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root (2 levels up from this script)
project_root = Path(__file__).parent.parent.parent
dotenv_path = project_root / ".env"
load_dotenv(dotenv_path)

# Only configurable settings - with validation
NODE_URL_RAW = os.getenv("NODE_URL")
if not NODE_URL_RAW:
    print("[ERROR] NODE_URL not set in .env file")
    print("[ERROR] Please set NODE_URL=http://localhost:8765 in .env")
    sys.exit(1)

NODE_URL = NODE_URL_RAW.rstrip("/")
MINER_ADDRESS = os.getenv("MINER_ADDRESS", "")

# Create directory for received files
RECEIVED_FILES_DIR = Path(__file__).parent / "received_files"
RECEIVED_FILES_DIR.mkdir(exist_ok=True)

class MinerStats:
    def __init__(self):
        self.blocks_mined = 0
        self.total_rewards = 0.0
        self.total_fees = 0.0
        self.start_time = time.time()
        
    def add_block(self, reward, fees):
        self.blocks_mined += 1
        self.total_rewards += reward
        self.total_fees += fees
        
    def get_uptime(self):
        return time.time() - self.start_time
        
    def print_stats(self):
        uptime = self.get_uptime()
        total_earned = self.total_rewards + self.total_fees
        print(f"Uptime: {uptime:.1f}s | Blocks: {self.blocks_mined} | Total Earned: {total_earned:.6f} PHN")

def log(message):
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def get_node_data():
    """Get all required data from node - WITH SECURITY VALIDATION"""
    try:
        # Get blockchain
        blockchain_resp = requests.post(f"{NODE_URL}/get_blockchain", timeout=10)
        blockchain_resp.raise_for_status()
        blockchain_data = blockchain_resp.json()
        
        # Get pending transactions
        pending_resp = requests.post(f"{NODE_URL}/get_pending", timeout=10)
        pending_resp.raise_for_status()
        pending_data = pending_resp.json()
        
        # Get mining parameters
        mining_resp = requests.get(f"{NODE_URL}/mining_info", timeout=10)
        mining_resp.raise_for_status()
        mining_data = mining_resp.json()
        
        # SECURITY: Validate all node data
        difficulty = mining_data.get("difficulty")
        block_reward = mining_data.get("block_reward")
        
        # Validate difficulty (must be integer 1-10)
        if not isinstance(difficulty, int) or difficulty < 1 or difficulty > 10:
            log(f"[SECURITY] Invalid difficulty from node: {difficulty}")
            return None
        
        # Validate block reward (must be positive, max 100 PHN)
        if not isinstance(block_reward, (int, float)) or block_reward <= 0 or block_reward > 100:
            log(f"[SECURITY] Invalid block reward from node: {block_reward}")
            return None
        
        return {
            "blockchain": blockchain_data.get("blockchain", []),
            "chain_length": blockchain_data.get("length", 0),
            "pending_txs": pending_data.get("pending_transactions", []),
            "difficulty": int(difficulty),  # Force integer
            "block_reward": float(block_reward),
            "owner_address": mining_data.get("owner_address"),
            "min_tx_fee": mining_data.get("min_tx_fee")
        }
    except Exception as e:
        log(f"Error getting node data: {e}")
        return None

def compute_hash(block):
    """Compute block hash - EXACT NODE IMPLEMENTATION"""
    block_copy = dict(block)
    block_copy.pop("hash", None)
    block_string = orjson.dumps(block_copy, option=orjson.OPT_SORT_KEYS)
    return hashlib.sha256(block_string).hexdigest()

def mine_block(block_template, target_difficulty):
    """Mine block with dynamic difficulty from node"""
    target_prefix = "0" * int(target_difficulty)
    start_time = time.time()
    hash_count = 0
    
    log(f"Mining block #{block_template['index']} - Target: {target_prefix}...")
    
    while True:
        # Generate random nonce
        block_template["nonce"] = random.randint(0, 2**31-1)
        
        # Compute hash
        block_hash = compute_hash(block_template)
        hash_count += 1
        
        # Check if hash meets difficulty
        if block_hash.startswith(target_prefix):
            block_template["hash"] = block_hash
            duration = time.time() - start_time
            hashrate = int(hash_count / duration) if duration > 0 else 0
            log(f"Block found! Hashes: {hash_count:,} | Time: {duration:.1f}s | Rate: {hashrate:,} H/s")
            return block_template
        
        # Progress indicator
        if hash_count % 10000 == 0:
            elapsed = time.time() - start_time
            hashrate = int(hash_count / elapsed) if elapsed > 0 else 0
            print(f"Mining... {hash_count:,} hashes | {hashrate:,} H/s", end='\r')

def create_coinbase_transaction(miner_address, reward_amount):
    """Create coinbase transaction - EXACT NODE FORMAT"""
    timestamp = time.time()
    txid = hashlib.sha256(f"coinbase_{miner_address}_{timestamp}".encode()).hexdigest()
    
    return {
        "sender": "coinbase",
        "recipient": miner_address,
        "amount": float(reward_amount),
        "fee": 0.0,
        "timestamp": timestamp,
        "txid": txid,
        "signature": "genesis"
    }

def create_fee_payout_transaction(miner_address, total_fees):
    """Create miners pool fee payout - Fees go to miner who mined the block"""
    timestamp = time.time()
    txid = hashlib.sha256(f"miners_pool_{miner_address}_{timestamp}".encode()).hexdigest()
    
    return {
        "sender": "miners_pool",
        "recipient": miner_address,
        "amount": float(total_fees),
        "fee": 0.0,
        "timestamp": timestamp,
        "txid": txid,
        "signature": "genesis"
    }

def build_block_template(node_data):
    """Build block template using ONLY node data"""
    blockchain = node_data["blockchain"]
    pending_txs = node_data["pending_txs"]
    block_reward = node_data["block_reward"]
    owner_address = node_data["owner_address"]
    chain_length = node_data["chain_length"]
    
    if not blockchain:
        log("ERROR: No blockchain data from node")
        return None
    
    # Calculate total fees from pending transactions
    total_fees = 0.0
    valid_pending_txs = []
    
    for tx in pending_txs:
        if tx.get("sender") not in ["coinbase", "miners_pool"]:
            valid_pending_txs.append(tx)
            total_fees += float(tx.get("fee", 0.0))
    
    # Build transaction list
    transactions = []
    
    # 1. Coinbase transaction (REQUIRED)
    coinbase_tx = create_coinbase_transaction(MINER_ADDRESS, block_reward)
    transactions.append(coinbase_tx)
    
    # 2. Add all valid pending transactions
    transactions.extend(valid_pending_txs)
    
    # 3. Add fee payout if there are fees - goes to miner
    if total_fees > 0:
        fee_payout_tx = create_fee_payout_transaction(MINER_ADDRESS, total_fees)
        transactions.append(fee_payout_tx)
    
    # Create block template
    last_block = blockchain[-1]
    block_template = {
        "index": chain_length,
        "timestamp": time.time(),
        "transactions": transactions,
        "prev_hash": last_block["hash"],
        "nonce": 0
    }
    
    log(f"Block template: {len(transactions)} transactions | Reward: {block_reward:.6f} PHN | Fees: {total_fees:.6f} PHN")
    
    return block_template, total_fees

def submit_block_to_node(block):
    """Submit mined block to node"""
    try:
        response = requests.post(f"{NODE_URL}/submit_block", 
                               json={"block": block}, 
                               timeout=15)
        
        if response.status_code == 200:
            return response.json()
        else:
            try:
                return response.json()
            except:
                return {"status": "error", "message": response.text}
                
    except Exception as e:
        return {"status": "error", "message": str(e)}

def validate_miner_setup():
    """Validate miner configuration"""
    if not MINER_ADDRESS:
        log("ERROR: MINER_ADDRESS not set in .env file")
        log("Please set MINER_ADDRESS=PHNyouraddresshere... in .env")
        return False
    
    if not MINER_ADDRESS.startswith("PHN") or len(MINER_ADDRESS) != 43:
        log("ERROR: Invalid MINER_ADDRESS format")
        log("MINER_ADDRESS must start with 'PHN' and be 43 characters long")
        return False
    
    # Test node connection
    try:
        response = requests.get(f"{NODE_URL}/", timeout=5)
        if response.status_code != 200:
            log(f"ERROR: Cannot connect to node at {NODE_URL}")
            return False
    except Exception as e:
        log(f"ERROR: Cannot connect to node: {e}")
        return False
    
    return True

def main():
    """Main mining loop - ALL PARAMETERS FROM NODE"""
    print("=" * 60)
    print("PHN NETWORK MINER")
    print("=" * 60)
    print(f"Node: {NODE_URL}")
    print(f"Miner: {MINER_ADDRESS}")
    print("=" * 60)
    print("All mining parameters are controlled by the node.")
    print("User cannot modify difficulty, rewards, or fees.")
    print("=" * 60)
    
    # Validate setup
    if not validate_miner_setup():
        return
    
    stats = MinerStats()
    consecutive_errors = 0
    max_errors = 5
    
    log("Starting miner - all parameters from node...")
    
    while True:
        try:
            # Get ALL data from node (no user control)
            node_data = get_node_data()
            if not node_data:
                log("Failed to get node data, retrying...")
                time.sleep(5)
                consecutive_errors += 1
                continue
            
            # Check if we have pending transactions
            # NOTE: We can mine empty blocks (just coinbase) to keep chain moving
            if not node_data["pending_txs"]:
                log("No pending transactions, mining empty block...")
                # Continue to mine, don't skip
            
            # Validate required parameters from node
            if node_data["difficulty"] is None or node_data["block_reward"] is None:
                log("ERROR: Node did not provide required mining parameters")
                time.sleep(5)
                consecutive_errors += 1
                continue
            
            # Build block template using ONLY node data
            template_result = build_block_template(node_data)
            if not template_result:
                log("Failed to build block template")
                time.sleep(5)
                continue
            
            block_template, total_fees = template_result
            
            # Mine block with node's difficulty
            log(f"Using node difficulty: {node_data['difficulty']}")
            log(f"Using node block reward: {node_data['block_reward']:.6f} PHN")
            
            mined_block = mine_block(block_template, node_data["difficulty"])
            
            # Verify hash locally
            local_hash = compute_hash(mined_block)
            if local_hash != mined_block.get("hash"):
                log("ERROR: Local hash verification failed")
                continue
            
            log(f"Block #{mined_block['index']} mined successfully")
            log(f"Hash: {mined_block['hash']}")
            
            # Submit to node
            log("Submitting block to node...")
            result = submit_block_to_node(mined_block)
            
            # Handle result
            if isinstance(result, dict) and result.get("status") in ["accepted", "success"]:
                stats.add_block(node_data["block_reward"], total_fees)
                log("SUCCESS: Block accepted by network!")
                log(f"Earned: {node_data['block_reward']:.6f} PHN (reward) + {total_fees:.6f} PHN (fees)")
                stats.print_stats()
                consecutive_errors = 0
            else:
                error_msg = result.get("message", "Unknown error") if isinstance(result, dict) else str(result)
                log(f"ERROR: Block rejected - {error_msg}")
                consecutive_errors += 1
            
            # Brief pause
            time.sleep(1)
            
        except requests.RequestException as e:
            log(f"Network error: {e}")
            consecutive_errors += 1
            time.sleep(5)
            
        except KeyboardInterrupt:
            print(f"\nMining stopped by user")
            stats.print_stats()
            break
            
        except Exception as e:
            log(f"Mining error: {e}")
            consecutive_errors += 1
            time.sleep(3)
        
        # Handle too many errors
        if consecutive_errors >= max_errors:
            log(f"Too many consecutive errors ({consecutive_errors}), taking extended break...")
            time.sleep(30)
            consecutive_errors = 0

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\nMining stopped by user")
