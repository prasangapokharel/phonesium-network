"""
LMDB Storage Layer for PHN Blockchain
Fast, scalable, embedded database with NO C++ compiler needed
Pure Python compatible, works on Windows/Linux/Mac
"""

import os
import orjson
import time
import lmdb
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

# Setup logging
logger = logging.getLogger(__name__)


class LMDBStorage:
    def __init__(self, db_dir: str = "lmdb_data", initial_map_size_mb: int = 1024):
        """
        Initialize LMDB connection with auto-resize capability

        Args:
            db_dir: Directory for LMDB files
            initial_map_size_mb: Initial database size in MB (default 1GB for production)
        """
        self.db_path = os.path.join(PROJECT_ROOT, db_dir)
        os.makedirs(self.db_path, exist_ok=True)

        # Store map size for resize operations
        self.current_map_size = initial_map_size_mb * 1024 * 1024
        self.max_map_size = 10 * 1024 * 1024 * 1024  # 10GB max

        # Open LMDB environment with multiple named databases
        self.env = lmdb.open(
            self.db_path,
            map_size=self.current_map_size,  # Start with 1GB (configurable)
            max_dbs=10,  # Support multiple named databases
            writemap=True,
            map_async=True,
            metasync=False,
        )

        # Create named databases
        with self.env.begin(write=True) as txn:
            self.blocks_db = self.env.open_db(b"blocks", txn=txn)
            self.pending_db = self.env.open_db(b"pending", txn=txn)
            self.peers_db = self.env.open_db(b"peers", txn=txn)
            self.metadata_db = self.env.open_db(b"metadata", txn=txn)
            self.validation_db = self.env.open_db(b"validation", txn=txn)
            self.balance_cache_db = self.env.open_db(b"balance_cache", txn=txn)

        logger.info(f"LMDB initialized at {self.db_path}")
        logger.info(
            f"Initial map size: {initial_map_size_mb}MB, Max size: {self.max_map_size / (1024 * 1024 * 1024):.1f}GB"
        )

    def _check_and_resize(self):
        """
        Check database usage and resize if necessary
        Auto-resize when 80% full
        """
        try:
            stat = self.env.stat()
            info = self.env.info()

            # Calculate usage percentage
            used_size = stat["psize"] * info["last_pgno"]
            usage_percent = (used_size / self.current_map_size) * 100

            # If over 80% full, double the size
            if usage_percent > 80:
                new_size = min(self.current_map_size * 2, self.max_map_size)
                if new_size > self.current_map_size:
                    logger.warning(
                        f"Database {usage_percent:.1f}% full, resizing to {new_size / (1024 * 1024):.0f}MB"
                    )
                    self.env.set_mapsize(new_size)
                    self.current_map_size = new_size
                    logger.info(f"Database resized successfully")
                else:
                    logger.error(f"Database at max size, cannot resize further")
        except Exception as e:
            logger.error(f"Error checking database size: {e}")

    def close(self):
        """Close LMDB connection"""
        if self.env:
            self.env.sync()
            self.env.close()
            logger.info("LMDB database closed")

    # ========== BLOCKCHAIN OPERATIONS ==========

    def save_blockchain(self, blockchain: List[Dict]) -> bool:
        """Save entire blockchain to LMDB"""
        try:
            # Check and resize if necessary before saving
            self._check_and_resize()

            with self.env.begin(write=True) as txn:
                # Clear existing blocks
                with txn.cursor(db=self.blocks_db) as cursor:
                    cursor.first()
                    while cursor.delete():
                        pass

                # Save new blocks
                for block in blockchain:
                    block_index = block.get("index", 0)
                    key = f"{block_index:010d}".encode()
                    value = orjson.dumps(block)
                    txn.put(key, value, db=self.blocks_db)

                # Save metadata
                metadata = {"block_count": len(blockchain), "last_updated": time.time()}
                txn.put(b"blockchain_meta", orjson.dumps(metadata), db=self.metadata_db)

            logger.info(f"Saved {len(blockchain)} blocks to LMDB")
            return True

        except Exception as e:
            logger.error(f"Error saving blockchain: {e}")
            return False

    def load_blockchain(self) -> Optional[List[Dict]]:
        """Load blockchain from LMDB"""
        try:
            blocks = []

            with self.env.begin(db=self.blocks_db) as txn:
                with txn.cursor() as cursor:
                    for key, value in cursor:
                        block = orjson.loads(value)
                        blocks.append(block)

            if not blocks:
                print("[LMDB] No blockchain found")
                return None

            # Sort by index to ensure correct order
            blocks.sort(key=lambda b: b.get("index", 0))

            logger.info(f"Loaded {len(blocks)} blocks")
            return blocks

        except Exception as e:
            logger.info(f"Error loading blockchain: {e}")
            return None

    def get_block_by_index(self, index: int) -> Optional[Dict]:
        """Get a specific block by index"""
        try:
            key = f"{index:010d}".encode()

            with self.env.begin(db=self.blocks_db) as txn:
                value = txn.get(key)

                if value:
                    return orjson.loads(value)
            return None

        except Exception as e:
            logger.info(f"Error getting block {index}: {e}")
            return None

    def get_block_count(self) -> int:
        """Get total number of blocks"""
        try:
            with self.env.begin(db=self.metadata_db) as txn:
                meta = txn.get(b"blockchain_meta")
                if meta:
                    metadata = orjson.loads(meta)
                    return metadata.get("block_count", 0)
            return 0
        except:
            return 0

    def append_block(self, block: Dict) -> bool:
        """
        Append a single block to blockchain (OPTIMIZED for mining)
        Faster than save_blockchain() when adding one block at a time

        Args:
            block: Block dictionary to append

        Returns:
            bool: Success status
        """
        try:
            block_index = block.get("index", 0)

            with self.env.begin(write=True) as txn:
                # Save block
                key = f"{block_index:010d}".encode()
                value = orjson.dumps(block)
                txn.put(key, value, db=self.blocks_db)

                # Update metadata
                metadata = {"block_count": block_index + 1, "last_updated": time.time()}
                txn.put(b"blockchain_meta", orjson.dumps(metadata), db=self.metadata_db)

            return True

        except Exception as e:
            logger.info(f"Error appending block: {e}")
            return False

    # ========== PENDING TRANSACTIONS ==========

    def save_pending_transactions(self, pending_txs: List[Dict]) -> bool:
        """Save pending transactions to LMDB"""
        try:
            with self.env.begin(write=True) as txn:
                # Clear existing pending transactions
                with txn.cursor(db=self.pending_db) as cursor:
                    cursor.first()
                    while cursor.delete():
                        pass

                # Save new pending transactions
                for i, tx in enumerate(pending_txs):
                    key = f"{i:010d}".encode()
                    value = orjson.dumps(tx)
                    txn.put(key, value, db=self.pending_db)

            logger.info(f"Saved {len(pending_txs)} pending transactions")
            return True

        except Exception as e:
            logger.info(f"Error saving pending transactions: {e}")
            return False

    def load_pending_transactions(self) -> List[Dict]:
        """Load pending transactions from LMDB"""
        try:
            pending_txs = []

            with self.env.begin(db=self.pending_db) as txn:
                with txn.cursor() as cursor:
                    for key, value in cursor:
                        tx = orjson.loads(value)
                        pending_txs.append(tx)

            logger.info(f"Loaded {len(pending_txs)} pending transactions")
            return pending_txs

        except Exception as e:
            logger.info(f"Error loading pending transactions: {e}")
            return []

    # ========== PEERS ==========

    def save_peers(self, peers: set) -> bool:
        """Save peers to LMDB"""
        try:
            with self.env.begin(write=True) as txn:
                # Clear existing peers
                with txn.cursor(db=self.peers_db) as cursor:
                    cursor.first()
                    while cursor.delete():
                        pass

                # Save new peers
                for i, peer in enumerate(peers):
                    key = f"{i:010d}".encode()
                    value = peer.encode()
                    txn.put(key, value, db=self.peers_db)

            logger.info(f"Saved {len(peers)} peers")
            return True

        except Exception as e:
            logger.info(f"Error saving peers: {e}")
            return False

    def load_peers(self) -> set:
        """Load peers from LMDB"""
        try:
            peers = set()

            with self.env.begin(db=self.peers_db) as txn:
                with txn.cursor() as cursor:
                    for key, value in cursor:
                        peer = value.decode()
                        peers.add(peer)

            logger.info(f"Loaded {len(peers)} peers")
            return peers

        except Exception as e:
            logger.info(f"Error loading peers: {e}")
            return set()

    # ========== PROOF OF UNIVERSAL VALIDATION (POUV) ==========

    def save_validation_record(self, txid: str, validation_data: Dict) -> bool:
        """Save POUV validation record for a transaction"""
        try:
            with self.env.begin(write=True) as txn:
                key = f"tx:{txid}".encode()
                value = orjson.dumps(validation_data)
                txn.put(key, value, db=self.validation_db)
            return True
        except Exception as e:
            logger.info(f"Error saving validation record: {e}")
            return False

    def save_validation_records_batch(self, records: List[Tuple[str, Dict]]) -> bool:
        """
        Save multiple POUV validation records in a single batch transaction
        OPTIMIZED: Use this for bulk validation saves instead of individual saves

        Args:
            records: List of (txid, validation_data) tuples

        Returns:
            bool: Success status
        """
        try:
            with self.env.begin(write=True) as txn:
                for txid, validation_data in records:
                    key = f"tx:{txid}".encode()
                    value = orjson.dumps(validation_data)
                    txn.put(key, value, db=self.validation_db)

            logger.info(f"Batch saved {len(records)} validation records")
            return True
        except Exception as e:
            logger.info(f"Error batch saving validation records: {e}")
            return False

    def get_validation_record(self, txid: str) -> Optional[Dict]:
        """Get POUV validation record for a transaction"""
        try:
            key = f"tx:{txid}".encode()

            with self.env.begin(db=self.validation_db) as txn:
                value = txn.get(key)

                if value:
                    return orjson.loads(value)
            return None
        except Exception as e:
            logger.info(f"Error getting validation record: {e}")
            return None

    def get_validation_count(self) -> int:
        """Get total number of validated transactions"""
        try:
            count = 0
            with self.env.begin(db=self.validation_db) as txn:
                with txn.cursor() as cursor:
                    for _ in cursor:
                        count += 1
            return count
        except:
            return 0

    # ========== BALANCE CACHE ==========

    def save_balance_cache(self, balance_cache: Dict[str, Dict]) -> bool:
        """
        Save balance cache to LMDB for fast balance lookups

        Args:
            balance_cache: Dict mapping address -> {balance: float, last_block: int}

        Returns:
            True if successful, False otherwise
        """
        try:
            with self.env.begin(write=True) as txn:
                # Clear existing cache
                with txn.cursor(db=self.balance_cache_db) as cursor:
                    cursor.first()
                    while cursor.delete():
                        pass

                # Save new cache entries
                for address, cache_data in balance_cache.items():
                    key = address.encode()
                    value = orjson.dumps(cache_data)
                    txn.put(key, value, db=self.balance_cache_db)

                # Save metadata about cache
                metadata = {
                    "cache_size": len(balance_cache),
                    "last_updated": time.time(),
                }
                txn.put(b"cache_meta", orjson.dumps(metadata), db=self.metadata_db)

            logger.info(f"Saved balance cache with {len(balance_cache)} addresses")
            return True

        except Exception as e:
            logger.error(f"Error saving balance cache: {e}")
            return False

    def load_balance_cache(self) -> Dict[str, Dict]:
        """
        Load balance cache from LMDB

        Returns:
            Dict mapping address -> {balance: float, last_block: int}
        """
        try:
            balance_cache = {}

            with self.env.begin(db=self.balance_cache_db) as txn:
                with txn.cursor() as cursor:
                    for key, value in cursor:
                        address = key.decode()
                        cache_data = orjson.loads(value)
                        balance_cache[address] = cache_data

            logger.info(f"Loaded balance cache with {len(balance_cache)} addresses")
            return balance_cache

        except Exception as e:
            logger.info(f"Error loading balance cache: {e}")
            return {}


# Global LMDB instance
_lmdb_storage = None


def get_lmdb() -> LMDBStorage:
    """Get or create global LMDB instance"""
    global _lmdb_storage
    if _lmdb_storage is None:
        _lmdb_storage = LMDBStorage()
    return _lmdb_storage


def close_lmdb():
    """Close global LMDB instance"""
    global _lmdb_storage
    if _lmdb_storage:
        _lmdb_storage.close()
        _lmdb_storage = None
