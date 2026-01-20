# Phonesium SDK

**Official Python SDK for PHN Blockchain**

Easy-to-use Python library for interacting with the PHN blockchain network. Create wallets, send transactions, mine blocks, and build blockchain applications with just a few lines of code.

## Features

✅ **Wallet Management**
- Create & import wallets
- AES-256 encryption for wallet storage
- Secure private key management
- ECDSA signature signing & verification

✅ **Blockchain Interaction**
- Send & receive PHN tokens
- Query balances & transaction history
- Search transactions by TXID
- Get blockchain info & statistics

✅ **Mining**
- Simple mining interface
- Automatic difficulty adjustment
- Mining statistics & rewards tracking

✅ **Developer Friendly**
- Clean, intuitive API
- Comprehensive error handling
- Type hints for IDE support
- Full documentation & examples

## Installation

```bash
# From source
cd phonesium
pip install -e .

# With development tools
pip install -e ".[dev]"
```

## Quick Start

### 1. Create a Wallet

```python
from phonesium import Wallet

# Create new wallet
wallet = Wallet.create()
print(f"Address: {wallet.address}")

# Save with encryption
wallet.save("my_wallet.json", password="secure_password_123")

# Load encrypted wallet
wallet = Wallet.load("my_wallet.json", password="secure_password_123")
```

### 2. Check Balance & Send Tokens

```python
from phonesium import PhonesiumClient, Wallet

# Connect to node
client = PhonesiumClient("http://localhost:8765")

# Load wallet
wallet = Wallet.load("my_wallet.json", password="password")

# Check balance
balance = client.get_balance(wallet.address)
print(f"Balance: {balance} PHN")

# Send tokens
txid = client.send_tokens(
    wallet=wallet,
    recipient="PHN1234567890abcdef...",
    amount=10.0,
    fee=0.02
)
print(f"Transaction: {txid}")
```

### 3. Mine Blocks

```python
from phonesium import Miner, Wallet

# Load wallet
wallet = Wallet.load("my_wallet.json", password="password")

# Create miner
miner = Miner(wallet, node_url="http://localhost:8765")

# Mine single block
result = miner.mine_block()

# Mine continuously
miner.mine_continuous(max_blocks=10)
```

## API Reference

### Wallet Class

#### `Wallet.create() -> Wallet`
Create a new wallet with random keys.

#### `Wallet.load(filepath, password=None) -> Wallet`
Load wallet from encrypted file.

#### `Wallet.save(filepath, password=None)`
Save wallet with optional AES-256 encryption.

#### `wallet.sign(data) -> str`
Sign data with private key, returns hex signature.

#### `wallet.get_private_key(show_warning=True) -> str`
Get private key with security warning.

#### `wallet.create_transaction(recipient, amount, fee=1.0) -> dict`
Create and sign a transaction.

### PhonesiumClient Class

#### `client.get_balance(address) -> float`
Get balance for an address.

#### `client.send_tokens(wallet, recipient, amount, fee=None) -> str`
Send tokens and return transaction ID.

#### `client.get_blockchain() -> List[Dict]`
Get entire blockchain.

#### `client.get_token_info() -> Dict`
Get token supply and statistics.

#### `client.search_transaction(txid) -> Dict`
Find transaction by TXID.

#### `client.get_address_transactions(address) -> list`
Get all transactions for an address.

### Miner Class

#### `miner.mine_block(timeout=60) -> Optional[Dict]`
Mine a single block with timeout.

#### `miner.mine_continuous(max_blocks=None, delay=1.0)`
Mine continuously until stopped or max_blocks reached.

#### `miner.get_stats() -> Dict`
Get miner statistics (blocks mined, rewards earned).

## Examples

See the `examples/` directory for complete working examples:

- `example_create_wallet.py` - Create wallet and check balance
- `example_complete.py` - All SDK features demonstrated

Run examples:
```bash
cd phonesium/examples
python example_create_wallet.py
python example_complete.py
```

## Security Best Practices

⚠️ **NEVER** share your private key with anyone!

✅ **DO:**
- Always use password encryption when saving wallets
- Use strong, unique passwords (20+ characters)
- Keep wallet files in secure locations
- Backup your wallet files safely
- Test with small amounts first

❌ **DON'T:**
- Store private keys in plaintext
- Commit wallet files to version control
- Share your wallet password
- Use the same password for multiple wallets

## Error Handling

The SDK provides specific exceptions for different error types:

```python
from phonesium import (
    PhonesiumClient,
    NetworkError,
    InsufficientBalanceError,
    InvalidTransactionError,
    InvalidAddressError,
    WalletError
)

try:
    client = PhonesiumClient("http://localhost:8765")
    balance = client.get_balance("PHN...")
except NetworkError as e:
    print(f"Network error: {e}")
except InvalidAddressError as e:
    print(f"Invalid address: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/phonesium/phonesium-sdk.git
cd phonesium-sdk

# Install in development mode with dev tools
pip install -e ".[dev]"

# Run tests
pytest

# Code formatting
black phonesium/

# Type checking
mypy phonesium/
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=phonesium --cov-report=html

# Run specific test file
pytest tests/test_wallet.py
```

## Requirements

- Python 3.8 or higher
- orjson >= 3.9.0
- requests >= 2.31.0
- ecdsa >= 0.18.0
- cryptography >= 41.0.0

## Architecture

```
phonesium/
├── core/              # Core modules
│   ├── __init__.py
│   ├── wallet.py      # Wallet management
│   ├── client.py      # API client
│   ├── miner.py       # Mining functionality
│   └── exceptions.py  # Custom exceptions
├── examples/          # Example scripts
│   ├── example_create_wallet.py
│   └── example_complete.py
├── utils/             # Utility functions (future)
├── __init__.py        # Package entry point
└── setup.py           # Installation script
```

## License

MIT License - see LICENSE file for details

## Support

- **Documentation:** https://docs.phonesium.network
- **GitHub:** https://github.com/phonesium/phonesium-sdk
- **Issues:** https://github.com/phonesium/phonesium-sdk/issues
- **Email:** support@phonesium.network

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new features
5. Ensure all tests pass
6. Submit a pull request

## Changelog

### Version 1.0.0 (Current)
- Initial release
- Wallet management with encryption
- Full blockchain API client
- Mining functionality
- Comprehensive error handling
- Complete documentation

---

**Made with ❤️ for the PHN Blockchain community**
