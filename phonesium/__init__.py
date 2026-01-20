"""
Phonesium - PHN Blockchain Python SDK
Easy-to-use library for interacting with PHN blockchain

Configuration:
    Change phonesium/core/config.py to set default NODE_URL for production

Usage:
    from phonesium import Wallet, PhonesiumClient, Miner

    # Create wallet
    wallet = Wallet.create()

    # Connect to node (uses config.DEFAULT_NODE_URL by default)
    client = PhonesiumClient()

    # Check balance
    balance = client.get_balance(wallet.address)

    # Send tokens
    tx = client.send_tokens(wallet, recipient="PHN...", amount=10.0)

    # Mine blocks
    miner = Miner(wallet)
    miner.mine_continuous(max_blocks=5)

    # Or use convenience functions:
    from phonesium import create_wallet, send, get_balance

    wallet = create_wallet()
    balance = get_balance(wallet.address)
    send(wallet, "PHN...", 10.0)
"""

from typing import Optional
from .core.config import DEFAULT_NODE_URL, VERSION, AUTHOR, EMAIL
from .core.client import PhonesiumClient
from .core.wallet import Wallet
from .core.miner import Miner
from .core.explorer import BlockchainExplorer
from .core.assets import AssetCreator, AssetType, create_asset
from .core.communication import TunnelClient
from .core.exceptions import (
    PhonesiumError,
    NetworkError,
    InsufficientBalanceError,
    InvalidTransactionError,
    InvalidAddressError,
    WalletError,
)

__version__ = VERSION
__author__ = AUTHOR
__email__ = EMAIL

# Default client instance (uses localhost:8765)
_default_client = None


def get_client(node_url: Optional[str] = None) -> PhonesiumClient:
    """
    Get or create default client instance

    Args:
        node_url: Optional custom node URL (default: http://localhost:8765)

    Returns:
        PhonesiumClient: Client instance
    """
    global _default_client
    if node_url:
        return PhonesiumClient(node_url)
    if _default_client is None:
        _default_client = PhonesiumClient()
    return _default_client


# Convenience functions
def create_wallet() -> Wallet:
    """
    Create a new wallet with random keys

    Returns:
        Wallet: New wallet instance
    """
    return Wallet.create()


def load_wallet(filepath: str, password: Optional[str] = None) -> Wallet:
    """
    Load wallet from file

    Args:
        filepath: Path to wallet file
        password: Password if wallet is encrypted

    Returns:
        Wallet: Loaded wallet instance
    """
    return Wallet.load(filepath, password)


def get_balance(address: str, node_url: Optional[str] = None) -> float:
    """
    Get balance for an address

    Args:
        address: PHN address
        node_url: Optional custom node URL

    Returns:
        float: Balance in PHN
    """
    client = get_client(node_url)
    return client.get_balance(address)


def send(
    wallet: Wallet,
    recipient: str,
    amount: float,
    fee: Optional[float] = None,
    node_url: Optional[str] = None,
) -> str:
    """
    Send PHN tokens

    Args:
        wallet: Sender wallet
        recipient: Recipient PHN address
        amount: Amount to send
        fee: Transaction fee (optional)
        node_url: Optional custom node URL

    Returns:
        str: Transaction ID
    """
    client = get_client(node_url)
    return client.send_tokens(wallet, recipient, amount, fee)


def start_miner(
    wallet: Wallet, node_url: Optional[str] = None, max_blocks: Optional[int] = None
):
    """
    Start mining blocks

    Args:
        wallet: Miner wallet (receives rewards)
        node_url: Optional custom node URL
        max_blocks: Maximum blocks to mine (None = continuous)

    Returns:
        Miner: Miner instance
    """
    client = get_client(node_url)
    miner = Miner(wallet, client.node_url)
    if max_blocks:
        miner.mine_continuous(max_blocks=max_blocks)
    else:
        miner.mine_continuous()
    return miner


def explorer(node_url: Optional[str] = None) -> PhonesiumClient:
    """
    Get blockchain explorer client

    Args:
        node_url: Optional custom node URL

    Returns:
        PhonesiumClient: Client for exploring blockchain
    """
    return get_client(node_url)


__all__ = [
    # Core classes
    "PhonesiumClient",
    "Wallet",
    "Miner",
    "BlockchainExplorer",
    "AssetCreator",
    "AssetType",
    "TunnelClient",
    # Exceptions
    "PhonesiumError",
    "NetworkError",
    "InsufficientBalanceError",
    "InvalidTransactionError",
    "InvalidAddressError",
    "WalletError",
    # Convenience functions
    "create_wallet",
    "load_wallet",
    "get_balance",
    "send",
    "start_miner",
    "explorer",
    "get_client",
    "create_asset",
]
