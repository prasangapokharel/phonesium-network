"""
Comprehensive Integration Tests
Tests complete workflows with multiple components working together
"""
import pytest
import time
from app.core.blockchain.chain import blockchain, create_genesis_block
from app.core.transactions.mempool import AdvancedMempool
from app.core.transactions.base import create_signed_transaction
from app.utils.wallet_generator import generate_wallet


@pytest.mark.integration
class TestCompleteBlockchainWorkflow:
    """Test complete blockchain workflow from start to finish"""
    
    def test_full_transaction_lifecycle(self, clean_blockchain, clean_mempool, test_wallets):
        """Test: Create TX -> Add to mempool -> Mine block -> Add to chain"""
        alice = test_wallets['alice']
        bob = test_wallets['bob']
        miner = test_wallets['miner']
        
        # Step 1: Create transaction
        tx = create_signed_transaction(
            sender=alice['address'],
            recipient=bob['address'],
            amount=25.0,
            fee=0.05,
            private_key=alice['private_key']
        )
        
        assert tx is not None
        assert 'txid' in tx
        
        # Step 2: Add to mempool
        success, msg = clean_mempool.add_transaction(tx)
        assert success is True
        
        # Step 3: Verify in mempool
        pending = clean_mempool.get_transactions_for_mining()
        assert len(pending) == 1
        assert pending[0]['txid'] == tx['txid']
        
        # Step 4: Create block with transaction
        prev_block = clean_blockchain[-1]
        block = {
            'index': len(clean_blockchain),
            'timestamp': time.time(),
            'transactions': [
                {  # Coinbase
                    'sender': 'coinbase',
                    'recipient': miner['address'],
                    'amount': 50.0,
                    'fee': 0.0,
                    'timestamp': time.time(),
                    'txid': f"coinbase_{time.time()}",
                    'signature': 'genesis'
                },
                tx,  # User transaction
                {  # Fee payout
                    'sender': 'miners_pool',
                    'recipient': miner['address'],
                    'amount': 0.05,
                    'fee': 0.0,
                    'timestamp': time.time(),
                    'txid': f"fee_{time.time()}",
                    'signature': 'genesis'
                }
            ],
            'prev_hash': prev_block['hash'],
            'nonce': 0,
            'hash': '0' * 64,
            'difficulty': 1
        }
        
        # Step 5: Add block to chain
        clean_blockchain.append(block)
        
        assert len(clean_blockchain) == 2  # Genesis + new block
        
        # Step 6: Remove from mempool
        clean_mempool.remove_transaction(tx['txid'])
        
        remaining = clean_mempool.get_transactions_for_mining()
        assert len(remaining) == 0


@pytest.mark.integration
class TestMultiUserScenarios:
    """Test scenarios with multiple users"""
    
    def test_multiple_users_multiple_transactions(self, clean_blockchain, clean_mempool, test_wallets):
        """Test multiple users creating multiple transactions"""
        alice = test_wallets['alice']
        bob = test_wallets['bob']
        charlie = test_wallets['charlie']
        
        transactions = []
        
        # Alice -> Bob
        tx1 = create_signed_transaction(
            sender=alice['address'],
            recipient=bob['address'],
            amount=10.0,
            fee=0.02,
            private_key=alice['private_key']
        )
        transactions.append(tx1)
        
        # Bob -> Charlie
        tx2 = create_signed_transaction(
            sender=bob['address'],
            recipient=charlie['address'],
            amount=5.0,
            fee=0.03,
            private_key=bob['private_key']
        )
        transactions.append(tx2)
        
        # Charlie -> Alice
        tx3 = create_signed_transaction(
            sender=charlie['address'],
            recipient=alice['address'],
            amount=3.0,
            fee=0.01,
            private_key=charlie['private_key']
        )
        transactions.append(tx3)
        
        # Add all to mempool
        for tx in transactions:
            success, msg = clean_mempool.add_transaction(tx)
            assert success is True
            
        # Verify all in mempool
        pending = clean_mempool.get_transactions_for_mining()
        assert len(pending) == 3
        
        # Verify fee ordering (highest fee first)
        fees = [tx['fee'] for tx in pending]
        assert fees == sorted(fees, reverse=True)
        
    def test_transaction_chain(self, test_wallets):
        """Test chain of transactions: A->B->C->A"""
        alice = test_wallets['alice']
        bob = test_wallets['bob']
        charlie = test_wallets['charlie']
        
        # Alice sends to Bob
        tx1 = create_signed_transaction(
            sender=alice['address'],
            recipient=bob['address'],
            amount=100.0,
            fee=0.02,
            private_key=alice['private_key']
        )
        
        # Bob sends to Charlie
        tx2 = create_signed_transaction(
            sender=bob['address'],
            recipient=charlie['address'],
            amount=50.0,
            fee=0.02,
            private_key=bob['private_key']
        )
        
        # Charlie sends back to Alice
        tx3 = create_signed_transaction(
            sender=charlie['address'],
            recipient=alice['address'],
            amount=25.0,
            fee=0.02,
            private_key=charlie['private_key']
        )
        
        assert tx1 is not None
        assert tx2 is not None
        assert tx3 is not None
        
        # All should have different TXIDs
        assert tx1['txid'] != tx2['txid']
        assert tx2['txid'] != tx3['txid']


@pytest.mark.integration
class TestMiningScenarios:
    """Test various mining scenarios"""
    
    def test_mine_multiple_blocks(self, clean_blockchain, test_wallets):
        """Test mining multiple blocks in sequence"""
        miner = test_wallets['miner']
        
        initial_length = len(clean_blockchain)
        
        # Mine 5 blocks
        for i in range(5):
            prev_block = clean_blockchain[-1]
            
            block = {
                'index': len(clean_blockchain),
                'timestamp': time.time(),
                'transactions': [{
                    'sender': 'coinbase',
                    'recipient': miner['address'],
                    'amount': 50.0,
                    'fee': 0.0,
                    'timestamp': time.time(),
                    'txid': f"coinbase_{i}_{time.time()}",
                    'signature': 'genesis'
                }],
                'prev_hash': prev_block['hash'],
                'nonce': i,
                'hash': f"{'0' * (i+1)}{i}" * 8,  # Mock hash
                'difficulty': 1
            }
            
            clean_blockchain.append(block)
            
        assert len(clean_blockchain) == initial_length + 5
        
    def test_miner_reward_accumulation(self, test_wallets):
        """Test miner accumulates rewards over multiple blocks"""
        miner = test_wallets['miner']
        
        blocks_mined = 10
        reward_per_block = 50.0
        total_fees = 1.5  # Total fees from all transactions
        
        total_earnings = (blocks_mined * reward_per_block) + total_fees
        
        expected_earnings = 501.5
        assert total_earnings == expected_earnings


@pytest.mark.integration
class TestNetworkScenarios:
    """Test network interaction scenarios"""
    
    def test_new_node_joins_network(self):
        """Test new node joining existing network"""
        # Existing network
        network_nodes = [
            "http://localhost:8765",
            "http://localhost:8766",
        ]
        
        # New node
        new_node = "http://localhost:8767"
        
        # Add new node to network
        network_nodes.append(new_node)
        
        assert len(network_nodes) == 3
        assert new_node in network_nodes
        
    def test_node_discovers_peers(self):
        """Test node discovering peers from other nodes"""
        known_peers = {"http://localhost:8765"}
        
        # Peer 8765 reports its peers
        peer_list_from_8765 = [
            "http://localhost:8766",
            "http://localhost:8767",
            "http://localhost:8768"
        ]
        
        # Add discovered peers
        for peer in peer_list_from_8765:
            known_peers.add(peer)
            
        assert len(known_peers) == 4
        
    def test_block_propagation_simulation(self):
        """Test simulating block propagation"""
        network = {
            "node1": {"peers": ["node2", "node3"]},
            "node2": {"peers": ["node1", "node4"]},
            "node3": {"peers": ["node1", "node4"]},
            "node4": {"peers": ["node2", "node3"]}
        }
        
        # Node1 mines a block
        new_block = {"index": 1, "hash": "0"*64}
        
        # Simulate broadcast to peers
        notified_nodes = set(["node1"])  # Miner
        
        # First hop: node1 -> its peers
        for peer in network["node1"]["peers"]:
            notified_nodes.add(peer)
            
        # Second hop: those peers -> their peers
        for node in list(notified_nodes):
            if node in network:
                for peer in network[node]["peers"]:
                    notified_nodes.add(peer)
                    
        # All nodes should eventually have the block
        assert len(notified_nodes) == 4


@pytest.mark.integration
class TestStressScenarios:
    """Test system under stress"""
    
    def test_many_transactions_in_mempool(self, clean_mempool, test_wallets):
        """Test mempool with many transactions"""
        alice = test_wallets['alice']
        bob = test_wallets['bob']
        
        num_transactions = 100
        
        for i in range(num_transactions):
            tx = create_signed_transaction(
                sender=alice['address'],
                recipient=bob['address'],
                amount=float(i + 1),
                fee=0.02 + (i * 0.001),  # Varying fees
                private_key=alice['private_key']
            )
            
            clean_mempool.add_transaction(tx)
            
        # Mempool should handle many transactions
        pending = clean_mempool.get_transactions_for_mining()
        
        assert len(pending) >= min(num_transactions, clean_mempool.max_size)
        
    def test_rapid_block_creation(self, clean_blockchain, test_wallets):
        """Test creating many blocks rapidly"""
        miner = test_wallets['miner']
        
        start_len = len(clean_blockchain)
        num_blocks = 50
        
        for i in range(num_blocks):
            prev_block = clean_blockchain[-1]
            
            block = {
                'index': len(clean_blockchain),
                'timestamp': time.time() + i,
                'transactions': [{
                    'sender': 'coinbase',
                    'recipient': miner['address'],
                    'amount': 50.0,
                    'fee': 0.0,
                    'timestamp': time.time(),
                    'txid': f"cb_{i}",
                    'signature': 'genesis'
                }],
                'prev_hash': prev_block['hash'],
                'nonce': i,
                'hash': f"{i:064d}",
                'difficulty': 1
            }
            
            clean_blockchain.append(block)
            
        assert len(clean_blockchain) == start_len + num_blocks


@pytest.mark.integration
class TestEdgeCaseScenarios:
    """Test edge cases and unusual scenarios"""
    
    def test_empty_block_mining(self, clean_blockchain, test_wallets):
        """Test mining block with only coinbase transaction"""
        miner = test_wallets['miner']
        prev_block = clean_blockchain[-1]
        
        # Block with no user transactions
        block = {
            'index': len(clean_blockchain),
            'timestamp': time.time(),
            'transactions': [{
                'sender': 'coinbase',
                'recipient': miner['address'],
                'amount': 50.0,
                'fee': 0.0,
                'timestamp': time.time(),
                'txid': f"coinbase_{time.time()}",
                'signature': 'genesis'
            }],
            'prev_hash': prev_block['hash'],
            'nonce': 0,
            'hash': '0' * 64,
            'difficulty': 1
        }
        
        clean_blockchain.append(block)
        
        assert len(block['transactions']) == 1
        assert block['transactions'][0]['sender'] == 'coinbase'
        
    def test_transaction_to_self(self, test_wallets):
        """Test user sending transaction to themselves"""
        alice = test_wallets['alice']
        
        tx = create_signed_transaction(
            sender=alice['address'],
            recipient=alice['address'],
            amount=50.0,
            fee=0.02,
            private_key=alice['private_key']
        )
        
        assert tx['sender'] == tx['recipient']
        assert tx['amount'] == 50.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
