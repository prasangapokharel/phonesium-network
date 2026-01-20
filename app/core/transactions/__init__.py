"""
PHN Blockchain - Transaction Handling & Validation

Complete transaction lifecycle management including creation, validation, 
signing, and mempool operations.

Modules:
    base: Core transaction functions (creation, signing, validation)
    secure: Secure transaction validation with anti-replay protection
    mempool: In-memory transaction pool management

Key Functions:
    - make_txid(): Generate transaction ID with nonce
    - sign_tx(): Sign transaction with private key
    - verify_tx_signature(): Verify transaction signature
    - validate_transaction(): Validate transaction structure
    - AdvancedMempool: In-memory transaction pool class
"""

from .base import (
    make_txid,
    sign_tx,
    verify_tx_signature,
    validate_transaction,
    validate_block,
    get_balance,
    calculate_total_mined,
    get_current_block_reward,
    create_transaction,
    generate_keypair,
    generate_address_from_public_key
)

from .mempool import AdvancedMempool

__all__ = [
    # Base functions
    "make_txid",
    "sign_tx",
    "verify_tx_signature",
    "validate_transaction",
    "validate_block",
    "get_balance",
    "calculate_total_mined",
    "get_current_block_reward",
    "create_transaction",
    "generate_keypair",
    "generate_address_from_public_key",
    # Mempool
    "AdvancedMempool"
]
