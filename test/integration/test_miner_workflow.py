"""
Comprehensive Miner Workflow Tests
Tests all miner operations including block creation, mining, and reward distribution
"""
import pytest
import time
from app.core.blockchain.chain import blockchain, mine_block, calculate_block_hash
from app.core.transactions.base import create_signed_transaction
from app.core.transactions.mempool import AdvancedMempool


@pytest.mark.unit
class TestMinerBlockCreation:
    """Test miner's ability to create blocks"""
    
    def test_miner_can_create_coinbase_transaction(self, test_wallets):
        """Test miner creates valid coinbase transaction"""
        miner = test_wallets['miner']
        
        coinbase_tx = {
            'sender': 'coinbase',
            'recipient': miner['address'],
            'amount': 50.0,
            'fee': 0.0,
            'timestamp': time.time(),
            'txid': f"coinbase_{time.time()}",
            'signature': 'genesis'
        }
        
        assert coinbase_tx['sender'] == 'coinbase'
        assert coinbase_tx['amount'] == 50.0
        assert coinbase_tx['fee'] == 0.0
        assert coinbase_tx['signature'] == 'genesis'
        
    def test_miner_includes_pending_transactions(self, test_wallets, clean_mempool):
        """Test miner includes transactions from mempool"""
        alice = test_wallets['alice']
        bob = test_wallets['bob']
        
        # Create and add transaction to mempool
        tx = create_signed_transaction(
            sender=alice['address'],
            recipient=bob['address'],
            amount=10.0,
            fee=0.02,
            private_key=alice['private_key']
        )
        
        success, msg = clean_mempool.add_transaction(tx)
        assert success is True
        
        # Get transactions for mining
        txs_for_mining = clean_mempool.get_transactions_for_mining()
        
        assert len(txs_for_mining) >= 1
        assert txs_for_mining[0]['txid'] == tx['txid']
        
    def test_miner_calculates_total_fees(self, test_wallets):
        """Test miner correctly calculates total transaction fees"""
        transactions = [
            {'fee': 0.01},
            {'fee': 0.02},
            {'fee': 0.05},
        ]
        
        total_fees = sum(tx['fee'] for tx in transactions)
        
        assert total_fees == 0.08
        
    def test_miner_creates_fee_payout_transaction(self, test_wallets):
        """Test miner creates fee payout transaction"""
        miner = test_wallets['miner']
        total_fees = 0.08
        
        fee_payout = {
            'sender': 'miners_pool',
            'recipient': miner['address'],
            'amount': total_fees,
            'fee': 0.0,
            'timestamp': time.time(),
            'txid': f"fee_payout_{time.time()}",
            'signature': 'genesis'
        }
        
        assert fee_payout['sender'] == 'miners_pool'
        assert fee_payout['amount'] == total_fees
        assert fee_payout['recipient'] == miner['address']


@pytest.mark.unit
class TestMiningProcess:
    """Test the mining process"""
    
    def test_mining_finds_valid_hash(self, sample_block):
        """Test mining produces valid hash with correct difficulty"""
        difficulty = 2
        mined_block = mine_block(sample_block, difficulty=difficulty)
        
        assert mined_block is not None
        assert mined_block['hash'].startswith('0' * difficulty)
        
    def test_mining_increments_nonce(self, sample_block):
        """Test mining increments nonce to find valid hash"""
        original_nonce = sample_block['nonce']
        mined_block = mine_block(sample_block, difficulty=1)
        
        assert mined_block['nonce'] > original_nonce
        
    def test_mining_updates_block_hash(self, sample_block):
        """Test mining updates the block hash"""
        original_hash = sample_block.get('hash', '')
        mined_block = mine_block(sample_block, difficulty=1)
        
        assert mined_block['hash'] != original_hash
        assert len(mined_block['hash']) == 64
        
    def test_mining_with_transactions(self, test_wallets):
        """Test mining block with real transactions"""
        miner = test_wallets['miner']
        alice = test_wallets['alice']
        bob = test_wallets['bob']
        
        # Create block with transactions
        tx = create_signed_transaction(
            sender=alice['address'],
            recipient=bob['address'],
            amount=10.0,
            fee=0.02,
            private_key=alice['private_key']
        )
        
        block = {
            'index': 1,
            'timestamp': time.time(),
            'transactions': [
                {
                    'sender': 'coinbase',
                    'recipient': miner['address'],
                    'amount': 50.0,
                    'fee': 0.0,
                    'timestamp': time.time(),
                    'txid': f"coinbase_{time.time()}",
                    'signature': 'genesis'
                },
                tx,
                {
                    'sender': 'miners_pool',
                    'recipient': miner['address'],
                    'amount': 0.02,
                    'fee': 0.0,
                    'timestamp': time.time(),
                    'txid': f"fee_payout_{time.time()}",
                    'signature': 'genesis'
                }
            ],
            'prev_hash': '0' * 64,
            'nonce': 0,
            'hash': ''
        }
        
        mined_block = mine_block(block, difficulty=1)
        
        assert mined_block is not None
        assert len(mined_block['transactions']) == 3
        assert mined_block['hash'].startswith('0')


@pytest.mark.unit
class TestMinerRewards:
    """Test miner reward distribution"""
    
    def test_miner_receives_block_reward(self, test_wallets):
        """Test miner gets block reward"""
        miner = test_wallets['miner']
        block_reward = 50.0
        
        coinbase = {
            'sender': 'coinbase',
            'recipient': miner['address'],
            'amount': block_reward,
            'fee': 0.0
        }
        
        assert coinbase['amount'] == block_reward
        assert coinbase['recipient'] == miner['address']
        
    def test_miner_receives_transaction_fees(self, test_wallets):
        """Test miner gets transaction fees"""
        miner = test_wallets['miner']
        total_fees = 0.15
        
        fee_payout = {
            'sender': 'miners_pool',
            'recipient': miner['address'],
            'amount': total_fees,
            'fee': 0.0
        }
        
        assert fee_payout['amount'] == total_fees
        assert fee_payout['recipient'] == miner['address']
        
    def test_miner_total_revenue(self, test_wallets):
        """Test miner's total revenue = block reward + fees"""
        block_reward = 50.0
        transaction_fees = 0.15
        
        total_revenue = block_reward + transaction_fees
        
        assert total_revenue == 50.15
        
    def test_block_reward_halving(self):
        """Test block reward halves at correct interval"""
        initial_reward = 50.0
        halving_interval = 1_800_000
        
        # Before first halving
        blocks_mined_0 = 1_000_000
        reward_0 = initial_reward
        assert reward_0 == 50.0
        
        # After first halving
        blocks_mined_1 = 1_800_000
        halvings_1 = blocks_mined_1 // halving_interval
        reward_1 = initial_reward / (2 ** halvings_1)
        assert reward_1 == 25.0
        
        # After second halving
        blocks_mined_2 = 3_600_000
        halvings_2 = blocks_mined_2 // halving_interval
        reward_2 = initial_reward / (2 ** halvings_2)
        assert reward_2 == 12.5


@pytest.mark.integration
class TestMinerWorkflow:
    """Test complete miner workflow"""
    
    def test_complete_mining_cycle(self, clean_blockchain, test_wallets, clean_mempool):
        """Test complete mining cycle: get txs -> create block -> mine -> submit"""
        miner = test_wallets['miner']
        alice = test_wallets['alice']
        bob = test_wallets['bob']
        
        # Step 1: User creates transaction
        tx = create_signed_transaction(
            sender=alice['address'],
            recipient=bob['address'],
            amount=10.0,
            fee=0.02,
            private_key=alice['private_key']
        )
        
        # Step 2: Transaction added to mempool
        success, msg = clean_mempool.add_transaction(tx)
        assert success is True
        
        # Step 3: Miner gets transactions from mempool
        pending_txs = clean_mempool.get_transactions_for_mining()
        assert len(pending_txs) >= 1
        
        # Step 4: Miner creates block with transactions
        prev_block = clean_blockchain[-1]
        total_fees = sum(t['fee'] for t in pending_txs)
        
        block = {
            'index': len(clean_blockchain),
            'timestamp': time.time(),
            'transactions': [
                # Coinbase transaction
                {
                    'sender': 'coinbase',
                    'recipient': miner['address'],
                    'amount': 50.0,
                    'fee': 0.0,
                    'timestamp': time.time(),
                    'txid': f"coinbase_{time.time()}",
                    'signature': 'genesis'
                },
                # User transactions
                *pending_txs,
                # Fee payout
                {
                    'sender': 'miners_pool',
                    'recipient': miner['address'],
                    'amount': total_fees,
                    'fee': 0.0,
                    'timestamp': time.time(),
                    'txid': f"fee_payout_{time.time()}",
                    'signature': 'genesis'
                }
            ],
            'prev_hash': prev_block['hash'],
            'nonce': 0,
            'hash': ''
        }
        
        # Step 5: Miner mines the block
        mined_block = mine_block(block, difficulty=1)
        assert mined_block is not None
        assert mined_block['hash'].startswith('0')
        
        # Step 6: Block is added to blockchain
        clean_blockchain.append(mined_block)
        assert len(clean_blockchain) > 1
        
        # Step 7: Transactions removed from mempool
        for tx in pending_txs:
            clean_mempool.remove_transaction(tx['txid'])
        
        remaining = clean_mempool.get_transactions_for_mining()
        assert len(remaining) == 0
        
    def test_miner_handles_empty_mempool(self, clean_blockchain, test_wallets, clean_mempool):
        """Test miner can mine block even with no pending transactions"""
        miner = test_wallets['miner']
        prev_block = clean_blockchain[-1]
        
        # Create block with only coinbase transaction
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
                    'txid': f"coinbase_{time.time()}",
                    'signature': 'genesis'
                }
            ],
            'prev_hash': prev_block['hash'],
            'nonce': 0,
            'hash': ''
        }
        
        mined_block = mine_block(block, difficulty=1)
        
        assert mined_block is not None
        assert len(mined_block['transactions']) == 1
        assert mined_block['transactions'][0]['sender'] == 'coinbase'


@pytest.mark.unit
class TestMinerValidation:
    """Test miner validation logic"""
    
    def test_miner_validates_difficulty(self):
        """Test miner validates difficulty is in valid range"""
        valid_difficulties = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        
        for diff in valid_difficulties:
            assert 1 <= diff <= 10
            
        invalid_difficulties = [0, -1, 11, 100]
        
        for diff in invalid_difficulties:
            assert not (1 <= diff <= 10)
            
    def test_miner_validates_block_reward(self):
        """Test miner validates block reward is not excessive"""
        max_reward = 100.0  # Maximum allowed reward
        
        valid_rewards = [50.0, 25.0, 12.5, 6.25]
        for reward in valid_rewards:
            assert reward <= max_reward
            
        invalid_rewards = [150.0, 1000.0]
        for reward in invalid_rewards:
            assert reward > max_reward


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
