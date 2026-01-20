"""
PHN Blockchain Miner for Phonesium SDK
Provides simple mining functionality
FIXED: Now matches node's exact block structure and hashing algorithm
"""

import hashlib
import time
import requests
import json
from typing import Dict, Optional, List

from .config import DEFAULT_NODE_URL, DEFAULT_MINING_TIMEOUT
from .wallet import Wallet
from .exceptions import NetworkError

try:
    import orjson

    HAS_ORJSON = True
except ImportError:
    orjson = None  # type: ignore
    HAS_ORJSON = False


class Miner:
    """
    Simple miner for PHN blockchain

    Example:
        >>> from phonesium.miner import Miner
        >>> from phonesium import Wallet
        >>>
        >>> wallet = Wallet.load("my_wallet.json", "password")
        >>> miner = Miner(wallet, node_url="http://localhost:8000")
        >>>
        >>> # Mine a single block
        >>> result = miner.mine_block()
        >>>
        >>> # Mine continuously
        >>> miner.mine_continuous(max_blocks=10)
    """

    def __init__(self, wallet: Wallet, node_url: str = DEFAULT_NODE_URL):
        """
        Initialize miner

        Args:
            wallet: Wallet to receive mining rewards
            node_url: URL of the blockchain node (default from config)
        """
        self.wallet = wallet
        self.node_url = (node_url or DEFAULT_NODE_URL).rstrip("/")
        self.blocks_mined = 0
        self.total_rewards = 0.0

        if not HAS_ORJSON:
            print("[WARNING] orjson not installed - using fallback json (slower)")
            print("[WARNING] Install with: pip install orjson")

    def _hash_block(self, block: Dict) -> str:
        """
        Hash a block using the EXACT same method as the node
        This is CRITICAL - must match node's hash_block() function exactly

        Args:
            block: Block dictionary (without 'hash' field)

        Returns:
            str: SHA256 hash of block
        """
        block_copy = dict(block)
        block_copy.pop("hash", None)  # Remove hash if present

        if HAS_ORJSON and orjson:
            # Use orjson with sorted keys (SAME AS NODE)
            import orjson as orj  # type: ignore

            block_string = orj.dumps(block_copy, option=orj.OPT_SORT_KEYS)  # type: ignore
        else:
            # Fallback to standard json with sorted keys
            block_string = json.dumps(block_copy, sort_keys=True).encode()

        return hashlib.sha256(block_string).hexdigest()

    def get_mining_info(self) -> Dict:
        """
        Get current mining difficulty and block info from node

        Returns:
            dict: Mining information including pending transactions
        """
        try:
            # Get node info
            response = requests.get(f"{self.node_url}/info")
            response.raise_for_status()
            info = response.json()

            # Get pending transactions for the block
            try:
                pending_response = requests.post(f"{self.node_url}/get_pending")
                pending_response.raise_for_status()
                pending_data = pending_response.json()
                pending_txs = pending_data.get("pending_transactions", [])
            except:
                pending_txs = []

            # Get blockchain to find last block hash
            try:
                blockchain_response = requests.post(f"{self.node_url}/get_blockchain")
                blockchain_response.raise_for_status()
                blockchain_data = blockchain_response.json()
                blockchain = blockchain_data.get("blockchain", [])
                last_block_hash = blockchain[-1]["hash"] if blockchain else "0" * 64
            except:
                last_block_hash = "0" * 64

            return {
                "difficulty": info.get("difficulty", 4),
                "height": info.get("height", 0),
                "last_block_hash": last_block_hash,
                "mining_reward": info.get("mining_reward", 50.0),
                "pending_transactions": pending_txs,
            }
        except requests.RequestException as e:
            raise NetworkError(f"Failed to get mining info: {e}")

    def mine_block(self, timeout: int = 60) -> Optional[Dict]:
        """
        Mine a single block with CORRECT structure matching the node

        Args:
            timeout: Maximum seconds to spend mining

        Returns:
            dict: Mining result with block info and reward
        """
        print(f"[MINER] Starting mining for address: {self.wallet.address}")

        # Get mining info and pending transactions
        mining_info = self.get_mining_info()
        difficulty = mining_info["difficulty"]
        target_prefix = "0" * difficulty
        pending_txs = mining_info["pending_transactions"]
        mining_reward = mining_info["mining_reward"]

        print(f"[MINER] Difficulty: {difficulty} (target: {target_prefix}...)")
        print(f"[MINER] Expected reward: {mining_reward} PHN")
        print(f"[MINER] Pending transactions: {len(pending_txs)}")

        # Build block structure (MUST MATCH NODE EXACTLY)
        prev_hash = mining_info["last_block_hash"]
        index = mining_info["height"]
        timestamp = time.time()
        miner_address = self.wallet.address

        # Create coinbase transaction (mining reward)
        coinbase_tx = {
            "sender": "coinbase",
            "recipient": miner_address,
            "amount": mining_reward,
            "fee": 0.0,
            "timestamp": timestamp,
            "txid": hashlib.sha256(
                f"coinbase_{miner_address}_{timestamp}_{index}".encode()
            ).hexdigest(),
            "signature": "genesis",
        }

        # Calculate total fees from pending transactions
        total_fees = sum(float(tx.get("fee", 0.0)) for tx in pending_txs)

        # Create fee transaction if there are fees
        transactions = [coinbase_tx]
        if total_fees > 0:
            fee_tx = {
                "sender": "miners_pool",
                "recipient": miner_address,
                "amount": total_fees,
                "fee": 0.0,
                "timestamp": timestamp,
                "txid": hashlib.sha256(
                    f"fees_{miner_address}_{timestamp}_{index}".encode()
                ).hexdigest(),
                "signature": "genesis",
            }
            transactions.append(fee_tx)

        # Add pending transactions to block
        transactions.extend(pending_txs)

        print(
            f"[MINER] Block will contain {len(transactions)} transactions (coinbase + {len(pending_txs)} pending)"
        )

        # Start mining
        nonce = 0
        start_time = time.time()
        hashes_tried = 0

        while True:
            # Check timeout
            elapsed = time.time() - start_time
            if elapsed > timeout:
                print(f"[MINER] Timeout reached after {elapsed:.2f}s")
                print(
                    f"[MINER] Tried {hashes_tried:,} hashes ({hashes_tried / elapsed:.0f} H/s)"
                )
                return None

            # Build block with current nonce
            block = {
                "index": index,
                "timestamp": timestamp,
                "transactions": transactions,
                "prev_hash": prev_hash,
                "nonce": nonce,
            }

            # Hash block using EXACT node method
            block_hash = self._hash_block(block)
            hashes_tried += 1

            # Progress indicator every 10000 hashes
            if hashes_tried % 10000 == 0:
                hashrate = hashes_tried / elapsed
                print(f"[MINER] Tried {hashes_tried:,} hashes ({hashrate:.0f} H/s)...")

            # Check if we found valid hash
            if block_hash.startswith(target_prefix):
                elapsed = time.time() - start_time
                hashrate = hashes_tried / elapsed

                # Add hash to block
                block["hash"] = block_hash

                print(f"\n[MINER] [OK] Block found!")
                print(f"[MINER] Hash: {block_hash}")
                print(f"[MINER] Nonce: {nonce}")
                print(f"[MINER] Time: {elapsed:.2f}s")
                print(f"[MINER] Hashrate: {hashrate:.0f} H/s")
                print(f"[MINER] Total hashes: {hashes_tried:,}")

                # Submit block to node (CORRECT ENDPOINT)
                try:
                    print(f"[MINER] Submitting block to node...")
                    response = requests.post(
                        f"{self.node_url}/submit_block",  # FIXED: was /mine
                        json={"block": block},
                        timeout=10,
                    )

                    if response.status_code == 200:
                        result = response.json()

                        self.blocks_mined += 1
                        self.total_rewards += mining_reward + total_fees

                        print(f"[MINER] [OK] Block accepted!")
                        print(
                            f"[MINER] Reward: {mining_reward} PHN + {total_fees} PHN fees"
                        )
                        print(f"[MINER] Total blocks mined: {self.blocks_mined}")
                        print(f"[MINER] Total rewards: {self.total_rewards} PHN")

                        return {
                            "success": True,
                            "block": block,
                            "reward": mining_reward + total_fees,
                            "time": elapsed,
                            "hashrate": hashrate,
                            "hashes": hashes_tried,
                        }
                    else:
                        print(f"[MINER] [ERROR] Block rejected: {response.text}")
                        return {
                            "success": False,
                            "block": block,
                            "error": response.text,
                        }

                except requests.RequestException as e:
                    print(f"[MINER] [ERROR] Failed to submit block: {e}")
                    return {"success": False, "block": block, "error": str(e)}

            nonce += 1

    def mine_continuous(self, max_blocks: Optional[int] = None, delay: float = 1.0):
        """
        Mine continuously until stopped or max_blocks reached

        Args:
            max_blocks: Maximum number of blocks to mine (None = infinite)
            delay: Delay in seconds between blocks
        """
        print(f"\n{'=' * 60}")
        print("PHN BLOCKCHAIN CONTINUOUS MINING")
        print(f"{'=' * 60}")
        print(f"Miner address: {self.wallet.address}")
        print(f"Node URL: {self.node_url}")

        if max_blocks:
            print(f"Target blocks: {max_blocks}")
        else:
            print("Target blocks: Infinite (press Ctrl+C to stop)")

        print(f"{'=' * 60}\n")

        blocks_to_mine = max_blocks if max_blocks else float("inf")
        blocks_mined_this_session = 0

        try:
            while blocks_mined_this_session < blocks_to_mine:
                print(f"\n[SESSION] Mining block {blocks_mined_this_session + 1}...")

                result = self.mine_block(timeout=300)  # 5 minute timeout per block

                if result and result.get("success"):
                    blocks_mined_this_session += 1
                    print(
                        f"\n[SESSION] Progress: {blocks_mined_this_session}/{blocks_to_mine if max_blocks else '∞'}"
                    )
                else:
                    print(
                        f"\n[SESSION] Failed to mine block, retrying after {delay}s..."
                    )

                # Delay before next block
                if blocks_mined_this_session < blocks_to_mine:
                    time.sleep(delay)

        except KeyboardInterrupt:
            print(f"\n\n[SESSION] Mining stopped by user")

        finally:
            print(f"\n{'=' * 60}")
            print("MINING SESSION SUMMARY")
            print(f"{'=' * 60}")
            print(f"Blocks mined this session: {blocks_mined_this_session}")
            print(f"Total blocks mined: {self.blocks_mined}")
            print(f"Total rewards earned: {self.total_rewards} PHN")
            print(f"{'=' * 60}\n")

    def get_stats(self) -> Dict:
        """
        Get miner statistics

        Returns:
            dict: Miner stats
        """
        return {
            "miner_address": self.wallet.address,
            "blocks_mined": self.blocks_mined,
            "total_rewards": self.total_rewards,
            "node_url": self.node_url,
        }

    def __repr__(self) -> str:
        return f"Miner(address={self.wallet.address}, blocks={self.blocks_mined}, rewards={self.total_rewards})"


# Example usage
if __name__ == "__main__":
    import sys

    print("PHN Blockchain Miner")
    print("=" * 60)
    print()
    print("This is a simple miner for the PHN blockchain.")
    print("To use it, you need:")
    print("  1. A wallet file (create with: python -m phonesium.wallet)")
    print("  2. A running node (start with: python app/main.py)")
    print()
    print("Example:")
    print("  >>> from phonesium.miner import Miner")
    print("  >>> from phonesium import Wallet")
    print("  >>> wallet = Wallet.load('my_wallet.json', 'password')")
    print("  >>> miner = Miner(wallet)")
    print("  >>> miner.mine_continuous(max_blocks=5)")
    print()
