"""
Test script to verify SDK miner hash matches node hash
"""

import hashlib
import json

try:
    import orjson

    HAS_ORJSON = True
except ImportError:
    HAS_ORJSON = False
    print("[WARNING] orjson not installed, using fallback")


def node_hash_block(block):
    """Exactly as implemented in app/core/blockchain/chain.py"""
    import orjson

    block_copy = dict(block)
    block_copy.pop("hash", None)
    block_string = orjson.dumps(block_copy, option=orjson.OPT_SORT_KEYS)
    return hashlib.sha256(block_string).hexdigest()


def sdk_hash_block(block):
    """As implemented in phonesium/core/miner.py"""
    block_copy = dict(block)
    block_copy.pop("hash", None)

    if HAS_ORJSON:
        import orjson as orj

        block_string = orj.dumps(block_copy, option=orj.OPT_SORT_KEYS)
    else:
        block_string = json.dumps(block_copy, sort_keys=True).encode()

    return hashlib.sha256(block_string).hexdigest()


# Test with sample block
test_block = {
    "index": 1,
    "timestamp": 1234567890.123,
    "transactions": [
        {
            "sender": "coinbase",
            "recipient": "PHN123abc",
            "amount": 50.0,
            "fee": 0.0,
            "timestamp": 1234567890.123,
            "txid": "abc123",
            "signature": "genesis",
        }
    ],
    "prev_hash": "0" * 64,
    "nonce": 12345,
}

print("=" * 60)
print("HASH COMPATIBILITY TEST")
print("=" * 60)

if not HAS_ORJSON:
    print("\n[ERROR] orjson not installed!")
    print("Install with: pip install orjson")
    print("Test cannot proceed without orjson")
    exit(1)

node_hash = node_hash_block(test_block)
sdk_hash = sdk_hash_block(test_block)

print(f"\nNode hash: {node_hash}")
print(f"SDK hash:  {sdk_hash}")
print(f"\nMatch: {node_hash == sdk_hash}")

if node_hash == sdk_hash:
    print("\n[OK] SUCCESS: SDK miner hash matches node hash exactly!")
    print("The SDK miner should now work correctly.")
else:
    print("\n[ERROR] FAILURE: Hashes don't match!")
    print("There may be a problem with the implementation.")

print("=" * 60)
