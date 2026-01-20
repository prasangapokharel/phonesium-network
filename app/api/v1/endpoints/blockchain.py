import orjson
import os
import time
import hashlib
import shutil
from filelock import FileLock
from ecdsa import VerifyingKey, SECP256k1, BadSignatureError
from app.core.config import settings
from app.core.blockchain.chain import load_owner_address
from app.utils.helpers import atomic_write, load_json, hash_block

# In-memory state
blockchain = []
pending_txs = []
address_book = {}  # display -> canonical
peers = set(settings.PEERS)  # peers populated from settings

ROOT = os.path.dirname(os.path.abspath(__file__))

# Persistence API
def save_blockchain():
    atomic_write(blockchain, settings.BLOCKCHAIN_FILE, settings.BLOCKCHAIN_LOCK)

def load_blockchain():
    global blockchain
    data = load_json(settings.BLOCKCHAIN_FILE)
    if not data:
        return False
    ok, reason = verify_blockchain(data)
    if not ok:
        print("Blockchain verification failed on load:", reason)
        return False
    blockchain[:] = data
    auto_bookmark_addresses()
    return True

def save_address_book():
    atomic_write(address_book, settings.ADDRESS_BOOK_FILE, settings.ADDRESS_BOOK_LOCK)

def load_address_book():
    global address_book
    data = load_json(settings.ADDRESS_BOOK_FILE)
    address_book.clear()
    address_book.update(data if isinstance(data, dict) else {})

# Address helpers
def canonical_to_display(canonical_public_key_hex: str) -> str:
    try:
        public_key_bytes = bytes.fromhex(canonical_public_key_hex)
        address_hash = hashlib.sha256(public_key_bytes).hexdigest()[:40]
        return f"PHN{address_hash}"
    except Exception:
        return ""

def register_address(display, canonical):
    address_book[display] = canonical
    save_address_book()

def resolve_display(display):
    return address_book.get(display)

def resolve_to_canonical(address):
    if not address:
        return None
    if address.startswith("PHN"):
        canonical = address_book.get(address)
        return canonical if canonical else address
    return address

def auto_bookmark_addresses():
    updated = False
    for block in blockchain:
        for tx in block.get("transactions", []):
            for addr in (tx.get("sender"), tx.get("recipient")):
                if not addr or addr in ("coinbase", "miners_pool"):
                    continue
                if addr not in address_book.values():
                    display = canonical_to_display(addr)
                    if display and display not in address_book:
                        address_book[display] = addr
                        updated = True
    if updated:
        print("[AutoBookmark] New addresses found and saved to address_book.json")
        save_address_book()

# Block helpers
def create_genesis_block():
    tx = {
        "sender": "coinbase",
        "recipient": load_owner_address(),
        "amount": settings.STARTING_BLOCK_REWARD * 1000000,
        "fee": 0.0,
        "timestamp": time.time(),
        "txid": hashlib.sha256(f"genesis_{load_owner_address()}_{time.time()}".encode()).hexdigest(),
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
    return blk

def verify_blockchain(chain):
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

# Signature validation
def validate_signature(tx):
    try:
        sig_hex = tx.get("signature", "")
        if not sig_hex or sig_hex == "genesis":
            return True  # genesis and no signature allowed
        sig = bytes.fromhex(sig_hex)
        sender_pub = tx.get("sender")
        if not sender_pub:
            return False
        vk = VerifyingKey.from_string(bytes.fromhex(sender_pub), curve=SECP256k1)
        tx_copy = dict(tx)
        tx_copy.pop("signature", None)
        tx_json = orjson.dumps(tx_copy, option=orjson.OPT_SORT_KEYS).encode()
        return vk.verify(sig, tx_json)
    except (BadSignatureError, Exception):
        return False

# Balances & halving
def get_balance(address):
    canonical_addr = resolve_to_canonical(address)
    if not canonical_addr:
        return 0.0
    bal = 0.0
    for block in blockchain:
        for tx in block.get("transactions", []):
            sender = resolve_to_canonical(tx.get("sender", ""))
            recipient = resolve_to_canonical(tx.get("recipient", ""))
            if recipient == canonical_addr:
                bal += float(tx.get("amount", 0.0))
            if sender == canonical_addr:
                bal -= (float(tx.get("amount", 0.0)) + float(tx.get("fee", 0.0)))
    for tx in pending_txs:
        sender = resolve_to_canonical(tx.get("sender", ""))
        recipient = resolve_to_canonical(tx.get("recipient", ""))
        if recipient == canonical_addr:
            bal += float(tx.get("amount", 0.0))
        if sender == canonical_addr:
            bal -= (float(tx.get("amount", 0.0)) + float(tx.get("fee", 0.0)))
    return bal

def calculate_total_mined():
    total = 0.0
    for block in blockchain:
        for tx in block.get("transactions", []):
            if tx.get("sender") == "coinbase":
                total += float(tx.get("amount", 0.0))
    return total

def get_current_block_reward():
    total_mined = calculate_total_mined()
    halvings = int(total_mined) // settings.HALVING_INTERVAL
    reward = settings.STARTING_BLOCK_REWARD / (2 ** halvings)
    return max(reward, 0.0001)

# Transaction & block validation
def validate_transaction(tx):
    required = ["sender", "recipient", "amount", "fee", "timestamp", "txid", "signature"]
    for r in required:
        if r not in tx:
            return False, f"Missing field: {r}"

    recomputed_txid = hashlib.sha256(
        f"{tx['sender']}{tx['recipient']}{tx['amount']}{tx['fee']}{tx['timestamp']}".encode()
    ).hexdigest()
    if recomputed_txid != tx["txid"]:
        return False, "Invalid txid"

    if tx["sender"] not in ("coinbase", "miners_pool"):
        if not validate_signature(tx):
            return False, "Invalid signature"

    if float(tx["amount"]) <= 0:
        return False, "Amount must be positive"

    if float(tx["fee"]) < settings.MIN_TX_FEE and tx["sender"] != "coinbase":
        return False, f"Fee too low; minimum {settings.MIN_TX_FEE}"

    if get_balance(tx["sender"]) < float(tx["amount"]) + float(tx["fee"]):
        return False, "Insufficient balance"

    return True, "ok"

def validate_block(block):
    if len(blockchain) > 0:
        last = blockchain[-1]
        if block["index"] != last["index"] + 1:
            return False, "Invalid index"
        if block["prev_hash"] != last["hash"]:
            return False, "prev_hash mismatch"
    else:
        if block["index"] != 0:
            return False, "Genesis index must be 0"

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
        found = False
        for tx in block.get("transactions", []):
            if tx.get("sender") == "miners_pool" and tx.get("recipient") == load_owner_address() and abs(float(tx.get("amount", 0.0)) - total_fees) < 1e-9:
                found = True
                break
        if not found:
            return False, "miners_pool fee payout to owner missing or incorrect"

    return True, "ok"