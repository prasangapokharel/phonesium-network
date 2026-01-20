"""
Phonesium Explorer - Blockchain Explorer and Analytics
Browse blocks, transactions, and network statistics
"""

import requests
from typing import Dict, List, Optional

from .config import DEFAULT_NODE_URL
from .exceptions import NetworkError


class BlockchainExplorer:
    """
    PHN Blockchain Explorer

    Browse and analyze blockchain data

    Example:
        >>> from phonesium import BlockchainExplorer
        >>>
        >>> explorer = BlockchainExplorer()
        >>>
        >>> # Get blockchain info
        >>> info = explorer.get_info()
        >>> print(f"Height: {info['height']}")
        >>>
        >>> # Get latest blocks
        >>> blocks = explorer.get_latest_blocks(10)
        >>>
        >>> # Search transaction
        >>> tx = explorer.get_transaction("abc123...")
        >>>
        >>> # Get address info
        >>> address_info = explorer.get_address_info("PHN...")
    """

    def __init__(self, node_url: str = None):
        """
        Initialize explorer

        Args:
            node_url: PHN node URL (default from config)
        """
        self.node_url = (node_url or DEFAULT_NODE_URL).rstrip("/")

    def get_info(self) -> Dict:
        """
        Get blockchain information

        Returns:
            dict: Blockchain info (height, difficulty, etc.)
        """
        try:
            response = requests.get(f"{self.node_url}/info", timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise NetworkError(f"Failed to get blockchain info: {e}")

    def get_blockchain(self) -> List[Dict]:
        """
        Get entire blockchain

        Returns:
            list: List of all blocks
        """
        try:
            response = requests.get(f"{self.node_url}/blockchain", timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise NetworkError(f"Failed to get blockchain: {e}")

    def get_block(self, index: int) -> Optional[Dict]:
        """
        Get block by index

        Args:
            index: Block height/index

        Returns:
            dict: Block data or None if not found
        """
        try:
            blockchain = self.get_blockchain()

            if 0 <= index < len(blockchain):
                return blockchain[index]
            else:
                return None
        except Exception as e:
            raise NetworkError(f"Failed to get block: {e}")

    def get_latest_blocks(self, count: int = 10) -> List[Dict]:
        """
        Get latest N blocks

        Args:
            count: Number of recent blocks to retrieve

        Returns:
            list: List of recent blocks
        """
        try:
            blockchain = self.get_blockchain()
            return blockchain[-count:] if len(blockchain) >= count else blockchain
        except Exception as e:
            raise NetworkError(f"Failed to get latest blocks: {e}")

    def get_transaction(self, txid: str) -> Optional[Dict]:
        """
        Search for transaction by TXID

        Args:
            txid: Transaction ID

        Returns:
            dict: Transaction data with block info or None if not found
        """
        try:
            blockchain = self.get_blockchain()

            for block in blockchain:
                for tx in block.get("transactions", []):
                    if tx.get("txid") == txid:
                        return {
                            "transaction": tx,
                            "block_index": block.get("index"),
                            "block_hash": block.get("hash"),
                            "timestamp": block.get("timestamp"),
                            "confirmed": True,
                        }

            return None
        except Exception as e:
            raise NetworkError(f"Failed to search transaction: {e}")

    def get_address_info(self, address: str) -> Dict:
        """
        Get complete information for an address

        Args:
            address: PHN address

        Returns:
            dict: Address info including balance, transactions, etc.
        """
        try:
            # Get balance
            balance_response = requests.post(
                f"{self.node_url}/get_balance", json={"address": address}, timeout=10
            )
            balance = (
                balance_response.json().get("balance", 0)
                if balance_response.status_code == 200
                else 0
            )

            # Get transactions
            blockchain = self.get_blockchain()
            transactions = []
            sent_total = 0.0
            received_total = 0.0

            for block in blockchain:
                for tx in block.get("transactions", []):
                    tx_sender = tx.get("sender", "")
                    tx_recipient = tx.get("recipient", "")

                    if tx_sender == address:
                        transactions.append(
                            {
                                "type": "sent",
                                "txid": tx.get("txid"),
                                "recipient": tx_recipient,
                                "amount": tx.get("amount", 0),
                                "fee": tx.get("fee", 0),
                                "timestamp": tx.get("timestamp"),
                                "block_index": block.get("index"),
                            }
                        )
                        sent_total += tx.get("amount", 0) + tx.get("fee", 0)

                    if tx_recipient == address:
                        transactions.append(
                            {
                                "type": "received",
                                "txid": tx.get("txid"),
                                "sender": tx_sender,
                                "amount": tx.get("amount", 0),
                                "timestamp": tx.get("timestamp"),
                                "block_index": block.get("index"),
                            }
                        )
                        received_total += tx.get("amount", 0)

            return {
                "address": address,
                "balance": balance,
                "total_received": received_total,
                "total_sent": sent_total,
                "transaction_count": len(transactions),
                "transactions": transactions,
            }

        except Exception as e:
            raise NetworkError(f"Failed to get address info: {e}")

    def get_address_transactions(self, address: str) -> List[Dict]:
        """
        Get all transactions for an address

        Args:
            address: PHN address

        Returns:
            list: List of transactions
        """
        try:
            address_info = self.get_address_info(address)
            return address_info.get("transactions", [])
        except Exception as e:
            raise NetworkError(f"Failed to get address transactions: {e}")

    def get_mempool(self) -> List[Dict]:
        """
        Get pending transactions in mempool

        Returns:
            list: List of pending transactions
        """
        try:
            response = requests.get(f"{self.node_url}/mempool", timeout=10)

            if response.status_code == 200:
                return response.json()
            else:
                return []
        except requests.RequestException as e:
            raise NetworkError(f"Failed to get mempool: {e}")

    def get_peers(self) -> List[str]:
        """
        Get list of connected peers

        Returns:
            list: List of peer URLs
        """
        try:
            response = requests.get(f"{self.node_url}/peers", timeout=10)

            if response.status_code == 200:
                return response.json()
            else:
                return []
        except requests.RequestException as e:
            raise NetworkError(f"Failed to get peers: {e}")

    def get_mining_info(self) -> Dict:
        """
        Get mining information

        Returns:
            dict: Mining info (difficulty, reward, etc.)
        """
        try:
            response = requests.get(f"{self.node_url}/mining_info", timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise NetworkError(f"Failed to get mining info: {e}")

    def get_token_info(self) -> Dict:
        """
        Get token information

        Returns:
            dict: Token info (supply, circulating, etc.)
        """
        try:
            response = requests.get(f"{self.node_url}/token_info", timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise NetworkError(f"Failed to get token info: {e}")

    def get_statistics(self) -> Dict:
        """
        Get comprehensive blockchain statistics

        Returns:
            dict: Blockchain statistics
        """
        try:
            info = self.get_info()
            blockchain = self.get_blockchain()
            mempool = self.get_mempool()

            total_transactions = sum(
                len(block.get("transactions", [])) for block in blockchain
            )

            return {
                "height": info.get("height", 0),
                "difficulty": info.get("difficulty", 0),
                "total_blocks": len(blockchain),
                "total_transactions": total_transactions,
                "pending_transactions": len(mempool),
                "avg_transactions_per_block": total_transactions / len(blockchain)
                if blockchain
                else 0,
                "last_block_time": blockchain[-1].get("timestamp")
                if blockchain
                else None,
                "network_hashrate": info.get("network_hashrate", "N/A"),
            }

        except Exception as e:
            raise NetworkError(f"Failed to get statistics: {e}")

    def search(self, query: str) -> Dict:
        """
        Universal search for address, transaction, or block

        Args:
            query: Search query (address, txid, or block index)

        Returns:
            dict: Search results
        """
        results = {"query": query, "type": None, "data": None}

        # Check if it's a block index
        if query.isdigit():
            block = self.get_block(int(query))
            if block:
                results["type"] = "block"
                results["data"] = block
                return results

        # Check if it's an address
        if query.startswith("PHN") and len(query) == 43:
            address_info = self.get_address_info(query)
            results["type"] = "address"
            results["data"] = address_info
            return results

        # Check if it's a transaction
        tx = self.get_transaction(query)
        if tx:
            results["type"] = "transaction"
            results["data"] = tx
            return results

        results["type"] = "not_found"
        return results

    def __repr__(self) -> str:
        return f"BlockchainExplorer(node={self.node_url})"
