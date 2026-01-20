"""
Pytest Configuration and Fixtures
Shared fixtures for all tests
"""
import pytest
import sys
import os
import time
import tempfile
import shutil
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.blockchain.chain import blockchain, create_genesis_block, init_database
from app.core.transactions.mempool import AdvancedMempool
from app.core.consensus.difficulty import DifficultyAdjuster
from app.core.transactions.base import generate_keypair, generate_address_from_public_key, create_transaction, sign_tx


@pytest.fixture(scope="session")
def test_db_path():
    """Create temporary database path for testing"""
    temp_dir = tempfile.mkdtemp(prefix="test_phn_")
    yield temp_dir
    # Cleanup after all tests
    try:
        shutil.rmtree(temp_dir)
    except:
        pass


@pytest.fixture(scope="function")
def clean_blockchain():
    """Provide a clean blockchain for each test"""
    # Save original blockchain
    original = blockchain.copy()
    
    # Reset to genesis
    blockchain.clear()
    blockchain.append(create_genesis_block())
    
    yield blockchain
    
    # Restore original
    blockchain.clear()
    blockchain.extend(original)


@pytest.fixture(scope="function")
def clean_mempool():
    """Provide a clean mempool for each test"""
    mempool = AdvancedMempool(max_size=10000, max_tx_age=3600)
    yield mempool


@pytest.fixture(scope="function")
def test_wallet():
    """Generate a test wallet"""
    private_key, public_key, address = generate_keypair()
    
    wallet = {
        'private_key': private_key,
        'public_key': public_key,
        'address': address
    }
    return wallet


@pytest.fixture(scope="function")
def test_wallets():
    """Generate multiple test wallets"""
    wallets = {}
    
    for name in ['alice', 'bob', 'charlie', 'miner']:
        private_key, public_key, address = generate_keypair()
        
        wallets[name] = {
            'private_key': private_key,
            'public_key': public_key,
            'address': address
        }
    
    return wallets


@pytest.fixture(scope="function")
def encrypted_wallet(tmp_path):
    """Create an encrypted test wallet"""
    # Generate wallet
    private_key, public_key, address = generate_keypair()
    
    wallet_path = tmp_path / "test_wallet.json"
    password = "TestPassword123!"
    
    # For testing, we'll just return the wallet data
    # Encryption test should be in separate unit test
    
    return {
        'path': str(wallet_path),
        'password': password,
        'address': address,
        'public_key': public_key,
        'private_key': private_key
    }


@pytest.fixture(scope="function")
def difficulty_adjuster():
    """Create a difficulty adjuster instance"""
    return DifficultyAdjuster(
        target_block_time=60,
        adjustment_interval=10
    )


@pytest.fixture(scope="function")
def sample_transaction(test_wallets):
    """Create a sample transaction"""
    alice = test_wallets['alice']
    bob = test_wallets['bob']
    
    tx = create_transaction(
        sender_private_key=alice['private_key'],
        sender_public_key=alice['public_key'],
        recipient_address=bob['address'],
        amount=10.0,
        fee=0.02
    )
    
    return tx


@pytest.fixture(scope="function")
def sample_block(clean_blockchain, test_wallets):
    """Create a sample block"""
    miner = test_wallets['miner']
    prev_block = clean_blockchain[-1]
    
    block = {
        'index': len(clean_blockchain),
        'timestamp': time.time(),
        'transactions': [
            {
                'sender': 'coinbase',
                'recipient': miner['address'],
                'amount': 50.0,
                'fee': 0.0,
                'timestamp': time.time(),
                'txid': 'coinbase_' + str(time.time()),
                'signature': 'genesis'
            }
        ],
        'prev_hash': prev_block['hash'],
        'nonce': 0,
        'hash': '0' * 64,
        'difficulty': 1
    }
    
    return block


@pytest.fixture(autouse=True)
def reset_test_state():
    """Automatically reset state before each test"""
    yield
    # Cleanup after each test
    pass


# Marks for organizing tests
def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line(
        "markers", "unit: Unit tests for individual components"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests for multiple components"
    )
    config.addinivalue_line(
        "markers", "security: Security-related tests"
    )
    config.addinivalue_line(
        "markers", "performance: Performance and benchmark tests"
    )
    config.addinivalue_line(
        "markers", "slow: Tests that take a long time to run"
    )
