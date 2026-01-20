"""
PHN Blockchain Core - With LMDB and Proof of Universal Validation (POUV)
Fast serialization with orjson
"""
import os
import time
import hashlib
import orjson
from typing import Dict, List, Optional, Tuple
from ecdsa import VerifyingKey, SECP256k1, BadSignatureError
from app.core.config import settings
from app.core.transactions.base import generate_keypair

try:
    from app.core.storage.lmdb import get_lmdb, close_lmdb
    LMDB_AVAILABLE = True
except ImportError:
    print("[CRITICAL] LMDB not available! Install with: pip install lmdb")
    LMDB_AVAILABLE = False
    raise ImportError("LMDB is REQUIRED for production. Install: pip install lmdb")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# In-memory cache for performance
blockchain = []
pending_txs = []
peers = set()

def init_database():
    """Initialize LMDB database"""
    if not LMDB_AVAILABLE:
        raise RuntimeError("LMDB is REQUIRED. Install: pip install lmdb")
    
    db = get_lmdb()
    print(f"[Blockchain] SUCCESS: LMDB initialized successfully")

def save_blockchain():
    """Save blockchain to LMDB using batch writes (OPTIMIZED)"""
    if not LMDB_AVAILABLE:
        raise RuntimeError("LMDB is REQUIRED for saving blockchain")
    
    db = get_lmdb()
    # Using batch writes as recommended in speedup.md
    db.save_blockchain(blockchain)

def load_blockchain():
    """Load blockchain from LMDB (NO JSON FALLBACK - LMDB ONLY)"""
    global blockchain
    
    if not LMDB_AVAILABLE:
        raise RuntimeError("LMDB is REQUIRED for loading blockchain")
    
    db = get_lmdb()
    loaded_blocks = db.load_blockchain()
    
    if not loaded_blocks:
        print("[startup] No blockchain found in LMDB - creating genesis block")
        genesis = create_genesis_block()
        blockchain.append(genesis)
        save_blockchain()
        print(f"[startup] Created genesis block with {settings.TOTAL_SUPPLY * 0.1} PHN allocated to company")
        return True
    
    print(f"[startup] Loading blockchain from LMDB...")
    print(f"[DEBUG] Raw data loaded: {len(loaded_blocks)} blocks")
    
    # Verify blockchain
    ok, reason = verify_blockchain(loaded_blocks)
    if not ok:
        print(f"[ERROR] Blockchain verification failed: {reason}")
        return False
    
    blockchain.clear()
    blockchain.extend(loaded_blocks)
    print(f"Successfully loaded and verified {len(blockchain)} blocks")
    print(f"[DEBUG] Blockchain state after loading: {len(blockchain)} blocks")
    print(f"[DEBUG] Loaded blocks: {[b.get('index') for b in blockchain]}")
    
    return True

def save_pending_transactions():
    """Save pending transactions to LMDB"""
    if not LMDB_AVAILABLE:
        return
    
    db = get_lmdb()
    db.save_pending_transactions(pending_txs)

def load_pending_transactions():
    """Load pending transactions from LMDB"""
    global pending_txs
    
    if not LMDB_AVAILABLE:
        return
    
    try:
        db = get_lmdb()
        loaded_txs = db.load_pending_transactions()
        pending_txs.clear()
        pending_txs.extend(loaded_txs)
    except Exception as e:
        print(f"[ERROR] Failed to load pending transactions: {e}")

def save_peers():
    """Save peers to LMDB"""
    if not LMDB_AVAILABLE:
        return
    
    db = get_lmdb()
    db.save_peers(peers)

def load_peers():
    """Load peers from LMDB"""
    global peers
    
    if not LMDB_AVAILABLE:
        return
    
    try:
        db = get_lmdb()
        loaded_peers = db.load_peers()
        peers.clear()
        peers.update(loaded_peers)
    except Exception as e:
        print(f"[ERROR] Failed to load peers: {e}")

def load_owner_address():
    """Load owner address from owner.txt"""
    owner_file = os.path.join(PROJECT_ROOT, "backups", "owner.txt")
    try:
        with open(owner_file, "r") as f:
            lines = f.read().splitlines()
            # Return the address (3rd line)
            return lines[2].strip() if len(lines) > 2 else ""
    except (FileNotFoundError, IndexError):
        return ""

def load_owner_private_key():
    """Load owner private key from owner.txt"""
    owner_file = os.path.join(PROJECT_ROOT, "backups", "owner.txt")
    try:
        with open(owner_file, "r") as f:
            lines = f.read().splitlines()
            # Return the private key (1st line)
            return lines[0].strip() if len(lines) > 0 else ""
    except (FileNotFoundError, IndexError):
        return ""

def load_owner_public_key():
    """Load owner public key from owner.txt"""
    owner_file = os.path.join(PROJECT_ROOT, "backups", "owner.txt")
    try:
        with open(owner_file, "r") as f:
            lines = f.read().splitlines()
            # Return the public key (2nd line)
            return lines[1].strip() if len(lines) > 1 else ""
    except (FileNotFoundError, IndexError):
        return ""

def generate_owner_wallet():
    """Generate a new owner wallet and save to owner.txt"""
    # Generate new keypair
    private_key, public_key, address = generate_keypair()
    
    # Save to owner.txt
    owner_file = os.path.join(PROJECT_ROOT, "backups", "owner.txt")
    os.makedirs(os.path.dirname(owner_file), exist_ok=True)
    
    with open(owner_file, "w") as f:
        f.write(f"{private_key}\n")
        f.write(f"{public_key}\n")
        f.write(f"{address}\n")
    
    print(f"[startup] Generated new owner wallet: {address}")
    print(f"[startup] Owner private key: {private_key}")
    
    return private_key, public_key, address

def create_genesis_block():
    """Create genesis block with 10% of total supply to newly generated company wallet"""
    # Check if owner wallet exists, if not generate new one
    owner_address = load_owner_address()
    if not owner_address:
        print("[startup] No owner wallet found, generating new one...")
        private_key, public_key, owner_address = generate_owner_wallet()
    else:
        print(f"[startup] Using existing owner wallet: {owner_address}")
    
    company_allocation = settings.TOTAL_SUPPLY * 0.1  # 100 million tokens
    
    tx = {
        "sender": "coinbase",
        "recipient": owner_address,
        "amount": company_allocation,
        "fee": 0.0,
        "timestamp": time.time(),
        "txid": hashlib.sha256(f"genesis_{owner_address}_{time.time()}".encode()).hexdigest(),
        "signature": "genesis"
    }
    
    blk = {
        "index": 0,
        "timestamp": time.time(),
        "transactions": [tx],
        "prev_hash": "0" * 64,
        "nonce": 0
    }
    
    blk["hash"] = hash_block(blk)
    
    # POUV: Record genesis block validation
    if LMDB_AVAILABLE:
        db = get_lmdb()
        db.save_validation_record(tx["txid"], {
            "txid": tx["txid"],
            "validated_at": time.time(),
            "validation_type": "genesis",
            "block_index": 0,
            "status": "valid"
        })
    
    return blk

def hash_block(block):
    """Calculate block hash"""
    block_copy = dict(block)
    block_copy.pop("hash", None)
    block_string = orjson.dumps(block_copy, option=orjson.OPT_SORT_KEYS)
    return hashlib.sha256(block_string).hexdigest()

def verify_blockchain(chain):
    """Verify blockchain integrity"""
    if not isinstance(chain, list) or not chain:
        return False, "chain must be a non-empty list"
    
    for i, b in enumerate(chain):
        if "hash" not in b:
            return False, f"block {i} missing hash"
        if b["hash"] != hash_block(b):
            return False, f"block {i} hash mismatch"
        if i > 0:
            if b["prev_hash"] != chain[i-1]["hash"]:
                return False, f"block {i} prev_hash mismatch"
    
    return True, "ok"

def validate_signature(tx):
    """
    Validate transaction signature - CRITICAL SECURITY
    NEVER allow empty or 'genesis' signatures for user transactions
    """
    try:
        sender = tx.get("sender", "")
        sig_hex = tx.get("signature", "")
        
        # Only system transactions can have special signatures
        if sender in ("coinbase", "miners_pool"):
            # System transactions must have 'genesis' signature
            if sig_hex == "genesis":
                return True
            else:
                print(f"[SECURITY] System transaction with invalid signature: {sender}")
                return False
        
        # USER TRANSACTIONS: MUST have valid signature
        if not sig_hex or sig_hex == "genesis":
            print(f"[SECURITY] User transaction missing signature or using system signature")
            return False
        
        # Verify signature
        sig = bytes.fromhex(sig_hex)
        sender_pub = tx.get("sender")
        if not sender_pub:
            return False
        
        vk = VerifyingKey.from_string(bytes.fromhex(sender_pub), curve=SECP256k1)
        tx_copy = dict(tx)
        tx_copy.pop("signature", None)
        tx_json = orjson.dumps(tx_copy, option=orjson.OPT_SORT_KEYS)
        
        verified = vk.verify(sig, tx_json)
        if verified:
            print(f"[SECURITY] Signature verified for tx {tx.get('txid', 'unknown')[:16]}...")
        return verified
    except (BadSignatureError, Exception) as e:
        print(f"[SECURITY] Signature verification failed: {e}")
        return False

def public_key_to_address(public_key_hex):
    """Convert public key to PHN address"""
    try:
        public_key_bytes = bytes.fromhex(public_key_hex)
        address_hash = hashlib.sha256(public_key_bytes).hexdigest()[:40]
        return f"PHN{address_hash}"
    except Exception:
        return ""

def get_balance(address):
    """Calculate balance for an address - handles both public keys and PHN addresses"""
    if not address:
        return 0.0
    
    # If the address is a public key (128 hex chars), convert to PHN address
    if len(address) == 128 and all(c in '0123456789abcdef' for c in address.lower()):
        # This is a public key, convert to PHN address for balance calculation
        phn_address = public_key_to_address(address)
        print(f"[DEBUG] Converting public key to PHN address: {address[:16]}... -> {phn_address}")
        address = phn_address
    
    bal = 0.0
    
    # Calculate from blockchain
    for block in blockchain:
        for tx in block.get("transactions", []):
            recipient = tx.get("recipient", "")
            sender = tx.get("sender", "")
            
            # Check if this address received tokens (exact match)
            if recipient == address:
                amount = float(tx.get("amount", 0.0))
                bal += amount
                print(f"[DEBUG] Found incoming tx: +{amount} PHN to {address}")
                
            # Check if this address sent tokens (exact match)
            if sender == address:
                amount = float(tx.get("amount", 0.0))
                fee = float(tx.get("fee", 0.0))
                bal -= (amount + fee)
                print(f"[DEBUG] Found outgoing tx: -{amount + fee} PHN from {address}")
            
            # Also check if sender is a public key and convert it to PHN address
            elif sender != "coinbase" and sender != "miners_pool" and len(sender) == 128:
                sender_phn_address = public_key_to_address(sender)
                if sender_phn_address == address:
                    amount = float(tx.get("amount", 0.0))
                    fee = float(tx.get("fee", 0.0))
                    bal -= (amount + fee)
                    print(f"[DEBUG] Found outgoing tx (pubkey converted): -{amount + fee} PHN from {address}")
    
    # Calculate from pending transactions
    for tx in pending_txs:
        recipient = tx.get("recipient", "")
        sender = tx.get("sender", "")
        
        if recipient == address:
            bal += float(tx.get("amount", 0.0))
        if sender == address:
            bal -= (float(tx.get("amount", 0.0)) + float(tx.get("fee", 0.0)))
        
        # Also check if sender is a public key and convert it to PHN address
        elif sender != "coinbase" and sender != "miners_pool" and len(sender) == 128:
            sender_phn_address = public_key_to_address(sender)
            if sender_phn_address == address:
                amount = float(tx.get("amount", 0.0))
                fee = float(tx.get("fee", 0.0))
                bal -= (amount + fee)
    
    print(f"[DEBUG] Final balance for {address}: {bal} PHN")
    return bal

def calculate_total_mined():
    """Calculate total tokens mined from coinbase transactions"""
    total = 0.0
    for block in blockchain:
        for tx in block.get("transactions", []):
            if tx.get("sender") == "coinbase":
                total += float(tx.get("amount", 0.0))
    return total

def get_current_block_reward():
    """
    Get current block reward with halving every 10% of supply mined.
    - Total minable: 900M PHN (90% of 1B total)
    - Each halving period: 90M PHN (10% of supply)
    - At 50 PHN/block: 1.8M blocks per halving
    - Halving schedule ensures fair distribution to miners
    """
    current_height = len(blockchain)
    halvings = current_height // settings.HALVING_INTERVAL  # Every 1.8M blocks
    
    initial_reward = settings.STARTING_BLOCK_REWARD  # 50.0 PHN
    reward = initial_reward / (2 ** halvings)
    return max(reward, 0.00001)  # Minimum reward to keep incentive

def make_txid(sender, recipient, amount, fee, timestamp, nonce=None):
    """
    Generate transaction ID - IMPROVED WITH NONCE
    Adding nonce prevents TXID collision attacks
    """
    # Include a random nonce to prevent collision
    if nonce is None:
        import random
        nonce = random.randint(0, 999999)
    
    hash_input = f"{sender}{recipient}{amount}{fee}{timestamp}{nonce}"
    
    print(f"[DEBUG] TXID generation (server):")
    print(f"[DEBUG]   Raw input: {hash_input}")
    
    txid = hashlib.sha256(hash_input.encode()).hexdigest()
    print(f"[DEBUG]   Generated TXID: {txid}")
    
    return txid

def validate_transaction_pouv(tx):
    """
    Proof of Universal Validation (POUV)
    Every transaction MUST pass through this validation
    ENHANCED WITH TIMESTAMP AND REPLAY PROTECTION
    """
    print(f"[POUV] Validating transaction: {tx.get('txid', 'NO_TXID')}")
    
    # Step 1: Check if transaction already validated or used
    if LMDB_AVAILABLE:
        db = get_lmdb()
        existing_validation = db.get_validation_record(tx.get("txid", ""))
        if existing_validation:
            if existing_validation.get("status") == "valid":
                # Check if this transaction is already in blockchain (replay protection)
                for block in blockchain:
                    for btx in block.get("transactions", []):
                        if btx.get("txid") == tx.get("txid"):
                            reason = "Transaction already in blockchain (replay attack detected)"
                            print(f"[SECURITY] {reason}")
                            return False, reason
                print(f"[POUV] Transaction already validated (but not yet in block)")
                return True, "ok"
            else:
                return False, f"Transaction previously rejected: {existing_validation.get('reason')}"
    
    # Step 2: Validate transaction structure
    required = ["sender", "recipient", "amount", "fee", "timestamp", "txid", "signature"]
    for r in required:
        if r not in tx:
            reason = f"Missing field: {r}"
            _save_pouv_record(tx.get("txid", "unknown"), "invalid", reason)
            return False, reason

    # Step 3: TIMESTAMP VALIDATION (Replay Attack Protection)
    current_time = time.time()
    tx_timestamp = float(tx.get("timestamp", 0))
    
    # Transaction must not be from the future (allow 60 second clock skew)
    if tx_timestamp > current_time + 60:
        reason = f"Transaction timestamp is in the future: {tx_timestamp} > {current_time}"
        print(f"[SECURITY] {reason}")
        _save_pouv_record(tx["txid"], "invalid", reason)
        return False, reason
    
    # Transaction must not be too old (prevent replay attacks)
    MAX_TX_AGE = 3600  # 1 hour
    if current_time - tx_timestamp > MAX_TX_AGE:
        reason = f"Transaction too old: {current_time - tx_timestamp} seconds (max {MAX_TX_AGE})"
        print(f"[SECURITY] {reason}")
        _save_pouv_record(tx["txid"], "invalid", reason)
        return False, reason

    # Step 4: SIGNATURE VALIDATION (must be done BEFORE balance check)
    if tx["sender"] not in ("coinbase", "miners_pool"):
        if not validate_signature(tx):
            reason = "Invalid signature"
            print(f"[SECURITY] {reason}")
            _save_pouv_record(tx["txid"], "invalid", reason)
            return False, reason

    # Step 5: For TXID validation
    # NOTE: We cannot regenerate TXID with nonce, so we just verify structure
    if not tx["txid"] or len(tx["txid"]) != 64:
        reason = "Invalid txid format"
        _save_pouv_record(tx["txid"], "invalid", reason)
        return False, reason

    # Step 6: Validate amount
    if float(tx["amount"]) <= 0:
        reason = "Amount must be positive"
        _save_pouv_record(tx["txid"], "invalid", reason)
        return False, reason

    # Step 7: Validate fee
    if float(tx["fee"]) < settings.MIN_TX_FEE and tx["sender"] not in ("coinbase", "miners_pool"):
        reason = f"Fee too low; minimum {settings.MIN_TX_FEE}"
        _save_pouv_record(tx["txid"], "invalid", reason)
        return False, reason

    # Step 8: Check balance - the get_balance function now handles public key conversion automatically
    sender = tx["sender"]
    if sender not in ("coinbase", "miners_pool"):
        sender_balance = get_balance(sender)  # This will auto-convert public key to PHN address
        total_needed = float(tx["amount"]) + float(tx["fee"])
        
        print(f"[POUV] Transaction validation - Sender: {sender[:16]}...")
        print(f"[POUV] Transaction validation - Balance: {sender_balance}")
        print(f"[POUV] Transaction validation - Needed: {total_needed}")
        
        if sender_balance < total_needed:
            reason = f"Insufficient balance. Need {total_needed}, have {sender_balance}"
            _save_pouv_record(tx["txid"], "invalid", reason)
            return False, reason

    # Step 9: Save validation record
    _save_pouv_record(tx["txid"], "valid", "All checks passed")
    
    print(f"[POUV] Transaction validation PASSED")
    return True, "ok"

def _save_pouv_record(txid, status, reason=""):
    """Save POUV validation record"""
    if not LMDB_AVAILABLE:
        return
    
    db = get_lmdb()
    db.save_validation_record(txid, {
        "txid": txid,
        "validated_at": time.time(),
        "validation_type": "pouv",
        "status": status,
        "reason": reason
    })

def validate_transaction(tx):
    """Main transaction validation - uses POUV"""
    return validate_transaction_pouv(tx)

def validate_block(block):
    """
    Validate a block with OPTIMIZED batch POUV validation
    Speedup: Uses batch writes for validation records (as per speedup.md)
    """
    # Step 1: Fast-fail checks (header validation first - as per speedup.md)
    if len(blockchain) > 0:
        last = blockchain[-1]
        if block["index"] != last["index"] + 1:
            return False, "Invalid index"
        if block["prev_hash"] != last["hash"]:
            return False, "prev_hash mismatch"
    else:
        if block["index"] != 0:
            return False, "Genesis index must be 0"

    # Verify hash early (reject 90% of bad blocks here)
    expected = hash_block(block)
    if block.get("hash") != expected:
        return False, "Hash mismatch"
    if not expected.startswith("0" * settings.DIFFICULTY):
        return False, f"Does not meet difficulty {settings.DIFFICULTY}"

    # Step 2: Validate transactions using POUV with BATCH writes
    coinbase_count = 0
    coinbase_amount = 0.0
    total_fees = 0.0
    seen = set()
    validation_records = []  # Collect validation records for batch write

    for tx in block.get("transactions", []):
        tid = tx.get("txid")
        if not tid or tid in seen:
            return False, "Duplicate or missing txid"
        seen.add(tid)
        
        if tx.get("sender") == "coinbase":
            coinbase_count += 1
            coinbase_amount += float(tx.get("amount", 0.0))
        elif tx.get("sender") == "miners_pool":
            continue
        else:
            # Use POUV for transaction validation
            ok, msg = validate_transaction_pouv(tx)
            if not ok:
                return False, f"Invalid tx in block: {msg}"
            total_fees += float(tx.get("fee", 0.0))
            
            # Collect validation record for batch write
            validation_records.append((tid, {
                "txid": tid,
                "validated_at": time.time(),
                "validation_type": "block",
                "block_index": block["index"],
                "status": "valid"
            }))

    # Step 3: Batch write validation records (OPTIMIZED - as per speedup.md)
    if validation_records and LMDB_AVAILABLE:
        db = get_lmdb()
        db.save_validation_records_batch(validation_records)

    # Step 4: Validate coinbase and fees
    if coinbase_count != 1:
        return False, "Exactly one coinbase tx required"

    expected_reward = get_current_block_reward()
    if abs(coinbase_amount - expected_reward) > 1e-9:
        return False, f"Coinbase must equal current reward {expected_reward}"

    if total_fees > 0:
        # Find miner address from coinbase transaction
        miner_address = None
        for tx in block.get("transactions", []):
            if tx.get("sender") == "coinbase":
                miner_address = tx.get("recipient")
                break
        
        if not miner_address:
            return False, "Cannot determine miner address from coinbase transaction"
        
        # Verify fees go to the miner (not owner)
        found = False
        for tx in block.get("transactions", []):
            if (tx.get("sender") == "miners_pool" and 
                tx.get("recipient") == miner_address and 
                abs(float(tx.get("amount", 0.0)) - total_fees) < 1e-9):
                found = True
                break
        if not found:
            return False, f"miners_pool fee payout to miner ({miner_address}) missing or incorrect"

    return True, "ok"
