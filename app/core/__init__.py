"""
PHN Blockchain - Core Application Layer

Modular, scalable blockchain core organized into logical subdirectories.

Architecture:
    blockchain/: Core blockchain operations & validation
    transactions/: Transaction handling, validation & mempool  
    storage/: Data persistence (LMDB with batch optimization)
    network/: P2P networking & node synchronization
    consensus/: Mining difficulty & consensus algorithms
    assets/: Asset tokenization & management (ERC-721/1155 principles)
    security/: Chain protection & validation
    extensions/: Optional features (tunnel transfer, etc.)

Performance Optimizations:
    - LMDB storage with 100% batch write compliance
    - orjson for 3-4x faster JSON operations
    - Memory-mapped I/O for zero-copy reads
    - In-memory mempool for fast transaction access
    - Optimized block validation pipeline

Usage:
    # Import directly from subdirectories
    from app.core.blockchain.chain import init_database, blockchain
    from app.core.transactions.base import make_txid, sign_tx
    from app.core.storage.lmdb import LMDBStorage, get_lmdb
    from app.core.network.sync import RobustNodeSync
    from app.core.consensus.difficulty import DifficultyAdjuster
    from app.core.assets.tokenization import Asset, AssetType
    from app.core.security.protection import ChainProtection
    from app.core.extensions.tunnel import TunnelTransferServer
"""

__version__ = "2.0.0"
__author__ = "PHN Blockchain Team"

# Config (stays in root)
from .config import settings

__all__ = [
    "settings"
]
