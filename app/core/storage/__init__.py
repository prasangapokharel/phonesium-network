"""
PHN Blockchain - Storage Layer

High-performance data persistence using LMDB (Lightning Memory-Mapped Database).

Modules:
    lmdb: LMDB storage implementation with batch write optimization

Features:
    - Lightning-fast read/write operations
    - Memory-mapped I/O for performance
    - Batch write optimization (10-100x faster)
    - ACID transactions
    - Zero-copy reads
    - Embedded database (no server needed)

Key Functions:
    - LMDBStorage: Main storage class
    - get_lmdb(): Get LMDB storage instance
    - close_lmdb(): Close LMDB connection
"""

from .lmdb import LMDBStorage, get_lmdb, close_lmdb

__all__ = [
    "LMDBStorage",
    "get_lmdb",
    "close_lmdb"
]
