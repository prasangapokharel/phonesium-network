# transactions.py - SECURE Core transaction logic for PHN blockchain
import hashlib
import orjson
import time
import random
from typing import Tuple
from ecdsa import VerifyingKey, SigningKey, SECP256k1, BadSignatureError
from app.core.config import settings
from app.utils.constants import blockchain, pending_txs, OWNER_ADDRESS

def make_txid(sender: str, recipient: str, amount: float, fee: float, timestamp: float = None, nonce: int = None) -> str:
    """
    Generate transaction ID with nonce to prevent collisions
    SECURITY: Adding nonce prevents TXID collision attacks
    """
    ts = timestamp or time.time()
    
    # Add random nonce if not provided
    if nonce is None:
        nonce = random.randint(0, 999999)
    
    s = f"{sender}{recipient}{amount}{fee}{ts}{nonce}"
    return hashlib.sha256(s.encode()).hexdigest()

def sign_tx(private_key_hex: str, tx_obj: dict) -> str:
    """Sign a transaction with private key"""
    sk = SigningKey.from_string(bytes.fromhex(private_key_hex), curve=SECP256k1)
    tx_copy = dict(tx_obj)
    tx_copy.pop("signature", None)
    tx_json = orjson.dumps(tx_copy, option=orjson.OPT_SORT_KEYS)
    return sk.sign(tx_json).hex()

def verify_tx_signature(tx_obj: dict) -> bool:
    """
    Verify transaction signature
    SECURITY: Strict signature verification
    """
    try:
        sender = tx_obj.get("sender", "")
        sig_hex = tx_obj.get("signature", "")
        
        # System transactions have special signatures
        if sender in ("coinbase", "miners_pool"):
            return sig_hex == "genesis"
        
        # User transactions MUST have valid signature
        if not sig_hex or sig_hex == "genesis":
            print(f"[SECURITY] User transaction missing signature")
            return False
        
        sig = bytes.fromhex(sig_hex)
        sender_pub_hex = tx_obj.get("sender")
        if not sender_pub_hex:
            return False
        
        vk = VerifyingKey.from_string(bytes.fromhex(sender_pub_hex), curve=SECP256k1)
        tx_copy = dict(tx_obj)
        tx_copy.pop("signature", None)
        tx_json = orjson.dumps(tx_copy, option=orjson.OPT_SORT_KEYS)
        return vk.verify(sig, tx_json)
    except (BadSignatureError, Exception) as e:
        print(f"[SECURITY] Signature verification failed: {e}")
        return False

def validate_transaction(tx: dict) -> tuple[bool, str]:
    """
    Validate a transaction with ENHANCED SECURITY
    """
    # Step 1: Structure validation
    required = ["sender", "recipient", "amount", "fee", "timestamp", "txid", "signature", "nonce"]
    for r in required:
        if r not in tx:
            return False, f"Missing field: {r}"
    
    # Step 2: Timestamp validation (REPLAY ATTACK PROTECTION)
    current_time = time.time()
    tx_timestamp = float(tx.get("timestamp", 0))
    
    # Transaction must not be from future
    if tx_timestamp > current_time + 60:  # 60 second clock skew
        return False, f"Transaction timestamp is in the future"
    
    # Transaction must not be too old (prevents replay)
    MAX_TX_AGE = 3600  # 1 hour
    if current_time - tx_timestamp > MAX_TX_AGE:
        return False, f"Transaction too old (replay protection)"
    
    # Step 3: Check if already in blockchain (REPLAY PROTECTION)
    for block in blockchain:
        for btx in block.get("transactions", []):
            if btx.get("txid") == tx.get("txid"):
                return False, "Transaction already in blockchain (replay attack)"
    
    # Step 4: TXID validation with nonce verification
    # SECURITY FIX: Verify TXID includes nonce to prevent collision
    recomputed_txid = make_txid(
        tx["sender"], 
        tx["recipient"], 
        tx["amount"], 
        tx["fee"], 
        tx["timestamp"], 
        tx.get("nonce")
    )
    if tx["txid"] != recomputed_txid:
        return False, f"Invalid txid - does not match transaction data"
    
    # Step 5: Signature validation (BEFORE balance check)
    if tx["sender"] not in ("coinbase", "miners_pool"):
        if not verify_tx_signature(tx):
            return False, "Invalid signature"
    
    # Step 6: Amount validation
    if float(tx["amount"]) <= 0:
        return False, "Amount must be positive"
    
    # Step 7: Fee validation
    if float(tx["fee"]) < settings.MIN_TX_FEE and tx["sender"] not in ("coinbase", "miners_pool"):
        return False, f"Fee too low; minimum {settings.MIN_TX_FEE}"
    
    # Step 8: Balance check
    if tx["sender"] not in ("coinbase", "miners_pool"):
        balance = get_balance(tx["sender"])
        total_needed = float(tx["amount"]) + float(tx["fee"])
        if balance < total_needed:
            return False, f"Insufficient balance. Need {total_needed}, have {balance}"

    return True, "ok"

def validate_block(block: dict) -> tuple[bool, str]:
    """Validate a block"""
    if len(blockchain) > 0:
        last = blockchain[-1]
        if block["index"] != last["index"] + 1:
            return False, "Invalid index"
        if block["prev_hash"] != last["hash"]:
            return False, "prev_hash mismatch"
    else:
        if block["index"] != 0:
            return False, "Genesis index must be 0"

    from app.utils.helpers import hash_block
    expected = hash_block(block)
    if block.get("hash") != expected:
        return False, "Hash mismatch"
    if not expected.startswith("0" * settings.DIFFICULTY):
        return False, f"Does not meet difficulty {settings.DIFFICULTY}"

    coinbase_count = 0
    coinbase_amount = 0.0
    total_fees = 0.0
    seen = set()

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
            ok, msg = validate_transaction(tx)
            if not ok:
                return False, f"Invalid tx in block: {msg}"
            total_fees += float(tx.get("fee", 0.0))

    if coinbase_count != 1:
        return False, "Exactly one coinbase tx required"

    expected_reward = get_current_block_reward()
    if abs(coinbase_amount - expected_reward) > 1e-9:
        return False, f"Coinbase must equal current reward {expected_reward}"

    if total_fees > 0:
        # Extract miner address from coinbase transaction
        miner_address = None
        for tx in block.get("transactions", []):
            if tx.get("sender") == "coinbase":
                miner_address = tx.get("recipient")
                break
        
        if not miner_address:
            return False, "Cannot determine miner address"
        
        # Verify fees go to miner (not owner)
        found = False
        for tx in block.get("transactions", []):
            if (tx.get("sender") == "miners_pool" and 
                tx.get("recipient") == miner_address and 
                abs(float(tx.get("amount", 0.0)) - total_fees) < 1e-9):
                found = True
                break
        if not found:
            return False, f"miners_pool fee payout to miner missing or incorrect"

    return True, "ok"

def get_balance(address: str) -> float:
    """Get balance for an address (simplified - no canonical resolution)"""
    if not address:
        return 0.0
    
    bal = 0.0
    for block in blockchain:
        for tx in block.get("transactions", []):
            sender = tx.get("sender", "")
            recipient = tx.get("recipient", "")
            if recipient == address:
                bal += float(tx.get("amount", 0.0))
            if sender == address:
                bal -= (float(tx.get("amount", 0.0)) + float(tx.get("fee", 0.0)))
    
    for tx in pending_txs:
        sender = tx.get("sender", "")
        recipient = tx.get("recipient", "")
        if recipient == address:
            bal += float(tx.get("amount", 0.0))
        if sender == address:
            bal -= (float(tx.get("amount", 0.0)) + float(tx.get("fee", 0.0)))
    
    return bal

def calculate_total_mined() -> float:
    """Calculate total tokens mined so far"""
    total = 0.0
    for block in blockchain:
        for tx in block.get("transactions", []):
            if tx.get("sender") == "coinbase":
                total += float(tx.get("amount", 0.0))
    return total

def get_current_block_reward() -> float:
    """Get current block reward with halving - SECURITY FIX: overflow protection"""
    total_mined = calculate_total_mined()
    halvings = int(total_mined) // settings.HALVING_INTERVAL
    # SECURITY FIX (Bug #4): Cap halvings to prevent overflow
    halvings = min(halvings, 100)  # After 100 halvings, reward is essentially 0
    reward = settings.STARTING_BLOCK_REWARD / (2 ** halvings)
    return max(reward, 0.0001)

def create_transaction(sender_private_key: str, sender_public_key: str, recipient_address: str, amount: float, fee: float = None) -> dict:
    """Create and sign a new transaction"""
    if fee is None:
        fee = settings.MIN_TX_FEE
    
    timestamp = time.time()
    nonce = random.randint(0, 999999)  # Add nonce for uniqueness
    txid = make_txid(sender_public_key, recipient_address, amount, fee, timestamp, nonce)
    
    tx = {
        "sender": sender_public_key,
        "recipient": recipient_address,
        "amount": amount,
        "fee": fee,
        "timestamp": timestamp,
        "txid": txid,
        "nonce": nonce,  # Include nonce in transaction
        "signature": ""
    }
    
    # Sign the transaction
    tx["signature"] = sign_tx(sender_private_key, tx)
    
    return tx

def generate_address_from_public_key(public_key_hex: str) -> str:
    """Generate PHN address from public key (simplified like Tron)"""
    try:
        public_key_bytes = bytes.fromhex(public_key_hex)
        address_hash = hashlib.sha256(public_key_bytes).hexdigest()[:40]
        return f"PHN{address_hash}"
    except Exception:
        return ""

def generate_keypair() -> Tuple[str, str, str]:
    """Generate new private key, public key, and address"""
    # Generate private key
    sk = SigningKey.generate(curve=SECP256k1)
    private_key = sk.to_string().hex()
    
    # Get public key
    vk = sk.get_verifying_key()
    public_key = vk.to_string().hex()
    
    # Generate address
    address = generate_address_from_public_key(public_key)
    
    return private_key, public_key, address
