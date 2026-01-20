"""
PHN Blockchain - Core Blockchain Operations

Main blockchain implementation with LMDB storage and Proof of Universal Validation (POUV).

Modules:
    chain: Main blockchain class and operations

Key Functions:
    - init_database(): Initialize LMDB database
    - load_blockchain(): Load blockchain from storage
    - save_blockchain(): Save blockchain to storage
    - create_genesis_block(): Create genesis block
    - verify_blockchain(): Verify blockchain integrity
    - validate_transaction(): Validate a transaction
    - validate_block(): Validate a block
    - get_balance(): Get balance for an address
"""

from .chain import (
    init_database,
    load_blockchain,
    save_blockchain,
    save_pending_transactions,
    load_pending_transactions,
    save_peers,
    load_peers,
    load_owner_address,
    load_owner_private_key,
    load_owner_public_key,
    generate_owner_wallet,
    create_genesis_block,
    hash_block,
    verify_blockchain,
    validate_signature,
    public_key_to_address,
    get_balance,
    calculate_total_mined,
    get_current_block_reward,
    make_txid,
    validate_transaction_pouv,
    validate_transaction,
    validate_block,
    blockchain,
    pending_txs,
    peers
)

__all__ = [
    "init_database",
    "load_blockchain",
    "save_blockchain",
    "save_pending_transactions",
    "load_pending_transactions",
    "save_peers",
    "load_peers",
    "load_owner_address",
    "load_owner_private_key",
    "load_owner_public_key",
    "generate_owner_wallet",
    "create_genesis_block",
    "hash_block",
    "verify_blockchain",
    "validate_signature",
    "public_key_to_address",
    "get_balance",
    "calculate_total_mined",
    "get_current_block_reward",
    "make_txid",
    "validate_transaction_pouv",
    "validate_transaction",
    "validate_block",
    "blockchain",
    "pending_txs",
    "peers"
]
