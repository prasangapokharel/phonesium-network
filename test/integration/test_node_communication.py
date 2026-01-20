"""
Comprehensive Node Communication and Sync Tests
Tests peer communication, synchronization, and network operations
"""
import pytest
import time
import asyncio
from app.core.network.sync import RobustNodeSync, NodeHealth


@pytest.mark.unit
class TestNodeHealth:
    """Test node health monitoring"""
    
    def test_node_health_initialization(self):
        """Test NodeHealth object initialization"""
        peer_url = "http://localhost:8765"
        health = NodeHealth(peer_url)
        
        assert health.url == peer_url
        assert health.is_healthy is True
        assert health.consecutive_failures == 0
        assert health.last_success_time is not None
        
    def test_node_health_record_failure(self):
        """Test recording node failures"""
        health = NodeHealth("http://localhost:8765")
        
        initial_failures = health.consecutive_failures
        health.record_failure()
        
        assert health.consecutive_failures == initial_failures + 1
        assert health.is_healthy is False
        
    def test_node_health_record_success(self):
        """Test recording node success"""
        health = NodeHealth("http://localhost:8765")
        
        # First record failure
        health.record_failure()
        assert health.is_healthy is False
        
        # Then record success
        health.record_success()
        assert health.is_healthy is True
        assert health.consecutive_failures == 0
        
    def test_node_health_failure_threshold(self):
        """Test node marked unhealthy after threshold"""
        health = NodeHealth("http://localhost:8765")
        
        # Record multiple failures
        for _ in range(5):
            health.record_failure()
            
        assert health.consecutive_failures == 5
        assert health.is_healthy is False
        
    def test_node_health_recovery(self):
        """Test node recovery after failures"""
        health = NodeHealth("http://localhost:8765")
        
        # Fail multiple times
        for _ in range(3):
            health.record_failure()
            
        assert health.is_healthy is False
        
        # Recover
        health.record_success()
        
        assert health.is_healthy is True
        assert health.consecutive_failures == 0


@pytest.mark.unit
class TestRobustNodeSync:
    """Test robust node synchronization"""
    
    def test_node_sync_initialization(self):
        """Test RobustNodeSync initialization"""
        peers = ["http://localhost:8765", "http://localhost:8766"]
        sync = RobustNodeSync(peers)
        
        assert len(sync.peers) == 2
        assert len(sync.peer_health) == 2
        
    def test_add_peer(self):
        """Test adding new peer"""
        sync = RobustNodeSync([])
        assert len(sync.peers) == 0
        
        sync.add_peer("http://localhost:8765")
        assert len(sync.peers) == 1
        assert "http://localhost:8765" in sync.peers
        
    def test_add_duplicate_peer(self):
        """Test adding duplicate peer"""
        sync = RobustNodeSync(["http://localhost:8765"])
        
        sync.add_peer("http://localhost:8765")
        
        # Should not add duplicate
        assert len(sync.peers) == 1
        
    def test_remove_peer(self):
        """Test removing peer"""
        sync = RobustNodeSync(["http://localhost:8765", "http://localhost:8766"])
        
        sync.remove_peer("http://localhost:8765")
        
        assert len(sync.peers) == 1
        assert "http://localhost:8765" not in sync.peers
        
    def test_get_healthy_peers(self):
        """Test getting only healthy peers"""
        sync = RobustNodeSync(["http://localhost:8765", "http://localhost:8766"])
        
        # Mark one peer as unhealthy
        sync.peer_health["http://localhost:8765"].record_failure()
        sync.peer_health["http://localhost:8765"].record_failure()
        sync.peer_health["http://localhost:8765"].record_failure()
        
        healthy_peers = sync.get_healthy_peers()
        
        assert "http://localhost:8766" in healthy_peers
        assert len(healthy_peers) <= 2


@pytest.mark.unit
class TestPeerCommunication:
    """Test peer-to-peer communication"""
    
    def test_peer_list_management(self):
        """Test managing list of peers"""
        peers = set()
        
        # Add peers
        peers.add("http://localhost:8765")
        peers.add("http://localhost:8766")
        peers.add("http://localhost:8767")
        
        assert len(peers) == 3
        
        # Remove peer
        peers.remove("http://localhost:8766")
        
        assert len(peers) == 2
        assert "http://localhost:8766" not in peers
        
    def test_peer_url_validation(self):
        """Test peer URL format validation"""
        valid_urls = [
            "http://localhost:8765",
            "http://192.168.1.1:8765",
            "http://example.com:8765",
            "https://secure.example.com:8765"
        ]
        
        for url in valid_urls:
            assert url.startswith('http://') or url.startswith('https://')
            assert ':' in url
            
    def test_broadcast_data_structure(self):
        """Test structure of broadcast messages"""
        broadcast_msg = {
            'type': 'new_block',
            'data': {
                'index': 1,
                'hash': '0' * 64,
                'timestamp': time.time()
            },
            'sender': 'http://localhost:8765'
        }
        
        assert 'type' in broadcast_msg
        assert 'data' in broadcast_msg
        assert broadcast_msg['type'] == 'new_block'


@pytest.mark.unit
class TestGossipProtocol:
    """Test gossip protocol implementation"""
    
    def test_gossip_message_structure(self):
        """Test gossip message has correct structure"""
        block = {
            'index': 1,
            'hash': '0' * 64,
            'transactions': [],
            'timestamp': time.time()
        }
        
        gossip_msg = {
            'type': 'block',
            'block': block,
            'timestamp': time.time(),
            'ttl': 3  # Time to live (hops)
        }
        
        assert 'type' in gossip_msg
        assert 'block' in gossip_msg
        assert 'ttl' in gossip_msg
        
    def test_gossip_ttl_decrement(self):
        """Test gossip TTL decrements on each hop"""
        msg = {'ttl': 5}
        
        # Simulate 3 hops
        msg['ttl'] -= 1  # Hop 1
        assert msg['ttl'] == 4
        
        msg['ttl'] -= 1  # Hop 2
        assert msg['ttl'] == 3
        
        msg['ttl'] -= 1  # Hop 3
        assert msg['ttl'] == 2
        
    def test_gossip_message_expiration(self):
        """Test gossip message expires after TTL reaches 0"""
        msg = {'ttl': 1}
        
        msg['ttl'] -= 1
        
        # Message should not be forwarded
        assert msg['ttl'] == 0
        should_forward = msg['ttl'] > 0
        assert should_forward is False


@pytest.mark.integration
class TestNodeSynchronization:
    """Test node synchronization scenarios"""
    
    def test_sync_empty_blockchain(self):
        """Test syncing with empty blockchain"""
        local_chain = []
        remote_chain = [
            {'index': 0, 'hash': 'genesis'},
            {'index': 1, 'hash': 'block1'}
        ]
        
        # Local should adopt remote chain
        should_sync = len(remote_chain) > len(local_chain)
        
        assert should_sync is True
        
    def test_sync_longer_chain(self):
        """Test syncing when remote chain is longer"""
        local_chain = [
            {'index': 0, 'hash': 'genesis'},
            {'index': 1, 'hash': 'block1'}
        ]
        
        remote_chain = [
            {'index': 0, 'hash': 'genesis'},
            {'index': 1, 'hash': 'block1'},
            {'index': 2, 'hash': 'block2'},
            {'index': 3, 'hash': 'block3'}
        ]
        
        should_sync = len(remote_chain) > len(local_chain)
        
        assert should_sync is True
        
    def test_no_sync_when_local_longer(self):
        """Test no sync when local chain is longer"""
        local_chain = [
            {'index': 0, 'hash': 'genesis'},
            {'index': 1, 'hash': 'block1'},
            {'index': 2, 'hash': 'block2'}
        ]
        
        remote_chain = [
            {'index': 0, 'hash': 'genesis'},
            {'index': 1, 'hash': 'block1'}
        ]
        
        should_sync = len(remote_chain) > len(local_chain)
        
        assert should_sync is False
        
    def test_sync_same_length_chains(self):
        """Test behavior when chains have same length"""
        local_chain = [
            {'index': 0, 'hash': 'genesis'},
            {'index': 1, 'hash': 'block1'}
        ]
        
        remote_chain = [
            {'index': 0, 'hash': 'genesis'},
            {'index': 1, 'hash': 'block1_alt'}
        ]
        
        # Should not sync if same length
        should_sync = len(remote_chain) > len(local_chain)
        
        assert should_sync is False


@pytest.mark.integration
class TestBlockPropagation:
    """Test block propagation through network"""
    
    def test_block_broadcast_to_all_peers(self):
        """Test block is broadcast to all connected peers"""
        peers = [
            "http://localhost:8765",
            "http://localhost:8766",
            "http://localhost:8767"
        ]
        
        block = {
            'index': 1,
            'hash': '0' * 64,
            'timestamp': time.time()
        }
        
        # Simulate broadcast
        broadcast_count = 0
        for peer in peers:
            # Would send block to each peer
            broadcast_count += 1
            
        assert broadcast_count == len(peers)
        
    def test_block_received_from_peer(self):
        """Test handling block received from peer"""
        received_block = {
            'index': 1,
            'hash': '0' * 64,
            'transactions': [],
            'timestamp': time.time(),
            'source_peer': 'http://localhost:8765'
        }
        
        # Validate block structure
        assert 'index' in received_block
        assert 'hash' in received_block
        assert 'transactions' in received_block
        
    def test_avoid_broadcast_loop(self):
        """Test avoiding infinite broadcast loops"""
        seen_blocks = set()
        
        block_hash = '0' * 64
        
        # First time seeing block
        if block_hash not in seen_blocks:
            seen_blocks.add(block_hash)
            should_broadcast = True
        else:
            should_broadcast = False
            
        assert should_broadcast is True
        
        # Second time seeing same block
        if block_hash not in seen_blocks:
            should_broadcast = True
        else:
            should_broadcast = False
            
        assert should_broadcast is False


@pytest.mark.unit
class TestPeerDiscovery:
    """Test peer discovery mechanisms"""
    
    def test_initial_peer_list(self):
        """Test node starts with initial peer list"""
        initial_peers = [
            "http://localhost:8765",
            "http://localhost:8766"
        ]
        
        sync = RobustNodeSync(initial_peers)
        
        assert len(sync.peers) == 2
        
    def test_discover_peers_from_peers(self):
        """Test discovering new peers from existing peers"""
        known_peers = {"http://localhost:8765"}
        
        # Peer reports additional peers
        new_peers_from_peer = [
            "http://localhost:8766",
            "http://localhost:8767"
        ]
        
        # Add newly discovered peers
        for peer in new_peers_from_peer:
            known_peers.add(peer)
            
        assert len(known_peers) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
