"""
Phonesium Client - Easy API client for PHN blockchain
"""

import hashlib
import orjson
import random
import time
from typing import Dict, List, Optional, Tuple
import requests
from ecdsa import SigningKey, SECP256k1

from .config import DEFAULT_NODE_URL, DEFAULT_TIMEOUT
from .wallet import Wallet
from .exceptions import (
    NetworkError,
    InsufficientBalanceError,
    InvalidTransactionError,
    InvalidAddressError,
)


class PhonesiumClient:
    """
    PHN Blockchain API Client

    Simple client for interacting with PHN blockchain nodes.

    Example:
        # Connect to node
        client = PhonesiumClient("http://localhost:8765")

        # Get balance
        balance = client.get_balance("PHN...")
        print(f"Balance: {balance} PHN")

        # Send tokens
        wallet = Wallet.load("wallet.json")
        txid = client.send_tokens(
            wallet=wallet,
            recipient="PHN...",
            amount=10.0,
            fee=0.02
        )
        print(f"Transaction: {txid}")
    """

    def __init__(self, node_url: str = None, timeout: int = None):
        """
        Initialize client

        Args:
            node_url: PHN node URL (default from config)
            timeout: Request timeout in seconds (default from config)
        """
        self.node_url = (node_url or DEFAULT_NODE_URL).rstrip("/")
        self.timeout = timeout or DEFAULT_TIMEOUT

    def get_balance(self, address: str) -> float:
        """
        Get balance for an address

        Args:
            address: PHN address

        Returns:
            float: Balance in PHN

        Raises:
            NetworkError: If API call fails
        """
        try:
            response = requests.post(
                f"{self.node_url}/get_balance",
                json={"address": address},
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            return float(data.get("balance", 0))
        except requests.RequestException as e:
            raise NetworkError(f"Failed to get balance: {e}")

    def send_tokens(
        self, wallet: Wallet, recipient: str, amount: float, fee: Optional[float] = None
    ) -> str:
        """
        Send PHN tokens

        Args:
            wallet: Sender wallet
            recipient: Recipient PHN address
            amount: Amount to send
            fee: Transaction fee (optional, uses minimum if not specified)

        Returns:
            str: Transaction ID

        Raises:
            InvalidAddressError: If recipient address is invalid
            InsufficientBalanceError: If wallet has insufficient balance
            InvalidTransactionError: If transaction is rejected
            NetworkError: If API call fails
        """
        # Validate recipient address
        if not self._is_valid_address(recipient):
            raise InvalidAddressError(f"Invalid recipient address: {recipient}")

        # Get minimum fee if not specified
        if fee is None:
            fee = self._get_minimum_fee()

        # Check balance
        balance = self.get_balance(wallet.address)
        total_needed = amount + fee
        if balance < total_needed:
            raise InsufficientBalanceError(
                f"Insufficient balance. Need {total_needed} PHN, have {balance} PHN"
            )

        # Create transaction
        tx = self._create_transaction(wallet, recipient, amount, fee)

        # Submit transaction
        try:
            response = requests.post(
                f"{self.node_url}/send_tx", json={"tx": tx}, timeout=self.timeout
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("txid", tx["txid"])
            else:
                error_msg = response.json().get("error", response.text)
                raise InvalidTransactionError(f"Transaction rejected: {error_msg}")

        except requests.RequestException as e:
            raise NetworkError(f"Failed to send transaction: {e}")

    def get_blockchain(self) -> List[Dict]:
        """
        Get entire blockchain

        Returns:
            List[Dict]: List of blocks

        Raises:
            NetworkError: If API call fails
        """
        try:
            response = requests.post(
                f"{self.node_url}/get_blockchain", timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            return data.get("blockchain", [])
        except requests.RequestException as e:
            raise NetworkError(f"Failed to get blockchain: {e}")

    def get_token_info(self) -> Dict:
        """
        Get token information

        Returns:
            Dict: Token info including supply, circulating, etc.

        Raises:
            NetworkError: If API call fails
        """
        try:
            response = requests.get(f"{self.node_url}/token_info", timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise NetworkError(f"Failed to get token info: {e}")

    def get_mining_info(self) -> Dict:
        """
        Get mining information

        Returns:
            Dict: Mining info including difficulty, reward, etc.

        Raises:
            NetworkError: If API call fails
        """
        try:
            response = requests.get(
                f"{self.node_url}/mining_info", timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise NetworkError(f"Failed to get mining info: {e}")

    def _create_transaction(
        self, wallet: Wallet, recipient: str, amount: float, fee: float
    ) -> Dict:
        """Create and sign a transaction"""
        timestamp = time.time()
        nonce = random.randint(0, 999999)

        tx = {
            "sender": wallet.public_key,
            "recipient": recipient,
            "amount": amount,
            "fee": fee,
            "timestamp": timestamp,
            "nonce": nonce,
            "signature": "",
        }

        # Generate TXID
        hash_input = f"{tx['sender']}{tx['recipient']}{tx['amount']}{tx['fee']}{tx['timestamp']}{tx['nonce']}"
        tx["txid"] = hashlib.sha256(hash_input.encode()).hexdigest()

        # Sign transaction
        tx_copy = dict(tx)
        tx_copy.pop("signature", None)
        tx_json = orjson.dumps(tx_copy, option=orjson.OPT_SORT_KEYS)
        tx["signature"] = wallet.sign(tx_json)

        return tx

    def _get_minimum_fee(self) -> float:
        """Get minimum transaction fee from node"""
        try:
            info = self.get_mining_info()
            return float(info.get("min_tx_fee", 0.02))
        except:
            return 0.02  # Default minimum fee

    @staticmethod
    def _is_valid_address(address: str) -> bool:
        """Validate PHN address format"""
        return (
            isinstance(address, str)
            and address.startswith("PHN")
            and len(address) == 43
        )

    def get_blockchain_info(self) -> Dict:
        """
        Get blockchain information (height, difficulty, etc.)

        Returns:
            dict: Blockchain information
        """
        try:
            response = requests.get(f"{self.node_url}/info")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise NetworkError(f"Failed to get blockchain info: {e}")

    def get_block(self, block_index: int) -> Dict:
        """
        Get block by index

        Args:
            block_index: Block height/index

        Returns:
            dict: Block data
        """
        try:
            response = requests.get(f"{self.node_url}/blockchain")
            response.raise_for_status()
            blockchain = response.json()

            if 0 <= block_index < len(blockchain):
                return blockchain[block_index]
            else:
                raise ValueError(f"Block index {block_index} out of range")
        except requests.RequestException as e:
            raise NetworkError(f"Failed to get block: {e}")

    def get_latest_blocks(self, count: int = 10) -> list:
        """
        Get latest N blocks from blockchain

        Args:
            count: Number of recent blocks to retrieve

        Returns:
            list: List of recent blocks
        """
        try:
            response = requests.get(f"{self.node_url}/blockchain")
            response.raise_for_status()
            blockchain = response.json()
            return blockchain[-count:] if len(blockchain) >= count else blockchain
        except requests.RequestException as e:
            raise NetworkError(f"Failed to get latest blocks: {e}")

    def search_transaction(self, txid: str) -> Dict:
        """
        Search for transaction by TXID across the blockchain

        Args:
            txid: Transaction ID to search for

        Returns:
            dict: Transaction data and block info
        """
        try:
            response = requests.get(f"{self.node_url}/blockchain")
            response.raise_for_status()
            blockchain = response.json()

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

            raise ValueError(f"Transaction {txid} not found in blockchain")
        except requests.RequestException as e:
            raise NetworkError(f"Failed to search transaction: {e}")

    def get_address_transactions(self, address: str) -> list:
        """
        Get all transactions for a specific address

        Args:
            address: PHN address to search for

        Returns:
            list: List of transactions (sent and received)
        """
        if not self._is_valid_address(address):
            raise InvalidAddressError(f"Invalid PHN address: {address}")

        try:
            response = requests.get(f"{self.node_url}/blockchain")
            response.raise_for_status()
            blockchain = response.json()

            transactions = []
            for block in blockchain:
                for tx in block.get("transactions", []):
                    if tx.get("sender") == address or tx.get("recipient") == address:
                        tx_data = tx.copy()
                        tx_data["block_index"] = block.get("index")
                        tx_data["block_timestamp"] = block.get("timestamp")
                        tx_data["type"] = (
                            "received" if tx.get("recipient") == address else "sent"
                        )
                        transactions.append(tx_data)

            return transactions
        except requests.RequestException as e:
            raise NetworkError(f"Failed to get address transactions: {e}")

    def get_mempool(self) -> list:
        """
        Get pending transactions in mempool

        Returns:
            list: List of pending transactions
        """
        try:
            response = requests.get(f"{self.node_url}/mempool")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise NetworkError(f"Failed to get mempool: {e}")

    def get_peers(self) -> list:
        """
        Get list of connected peers

        Returns:
            list: List of peer URLs
        """
        try:
            response = requests.get(f"{self.node_url}/peers")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise NetworkError(f"Failed to get peers: {e}")

    def __repr__(self) -> str:
        return f"PhonesiumClient(node={self.node_url})"
