"""
PHN Blockchain - Robust Node Sync with Failure Handling
This module implements high-availability node synchronization
"""
import asyncio
import time
from typing import List, Dict, Set
import requests

class NodeHealth:
    """Track node health and failures"""
    def __init__(self):
        self.peer_health: Dict[str, Dict] = {}
        self.failed_peers: Set[str] = set()
        self.max_failures = 3
        self.health_check_interval = 60  # seconds
        
    def mark_success(self, peer_url: str):
        """Mark a peer as healthy"""
        if peer_url not in self.peer_health:
            self.peer_health[peer_url] = {
                "failures": 0,
                "last_success": time.time(),
                "last_failure": None,
                "status": "healthy"
            }
        else:
            self.peer_health[peer_url]["failures"] = 0
            self.peer_health[peer_url]["last_success"] = time.time()
            self.peer_health[peer_url]["status"] = "healthy"
            
        # Remove from failed list
        self.failed_peers.discard(peer_url)
    
    def mark_failure(self, peer_url: str):
        """Mark a peer as failed"""
        if peer_url not in self.peer_health:
            self.peer_health[peer_url] = {
                "failures": 1,
                "last_success": None,
                "last_failure": time.time(),
                "status": "degraded"
            }
        else:
            self.peer_health[peer_url]["failures"] += 1
            self.peer_health[peer_url]["last_failure"] = time.time()
            
        # If too many failures, mark as failed
        if self.peer_health[peer_url]["failures"] >= self.max_failures:
            self.peer_health[peer_url]["status"] = "failed"
            self.failed_peers.add(peer_url)
            print(f"[health] Peer {peer_url} marked as FAILED after {self.max_failures} failures")
    
    def is_healthy(self, peer_url: str) -> bool:
        """Check if peer is healthy"""
        if peer_url in self.failed_peers:
            return False
        if peer_url not in self.peer_health:
            return True  # Unknown peers are assumed healthy
        return self.peer_health[peer_url]["status"] != "failed"
    
    def get_healthy_peers(self, all_peers: Set[str]) -> List[str]:
        """Get list of healthy peers"""
        return [p for p in all_peers if self.is_healthy(p)]
    
    def get_stats(self) -> Dict:
        """Get health statistics"""
        healthy = sum(1 for p in self.peer_health.values() if p["status"] == "healthy")
        degraded = sum(1 for p in self.peer_health.values() if p["status"] == "degraded")
        failed = len(self.failed_peers)
        
        return {
            "healthy_peers": healthy,
            "degraded_peers": degraded,
            "failed_peers": failed,
            "total_tracked": len(self.peer_health)
        }
    
    def try_recover_peers(self):
        """Try to recover failed peers"""
        recovered = []
        for peer_url in list(self.failed_peers):
            # Try to ping the peer
            try:
                url = peer_url.rstrip("/") + "/api/v1/info"
                res = requests.get(url, timeout=3)
                if res.status_code == 200:
                    print(f"[health] Peer {peer_url} recovered!")
                    self.mark_success(peer_url)
                    recovered.append(peer_url)
            except:
                pass
        return recovered


class RobustNodeSync:
    """
    Robust node synchronization with failure handling
    
    Features:
    - Health monitoring
    - Automatic peer recovery
    - Fallback sync strategies
    - Network partition detection
    """
    
    def __init__(self, blockchain, peers, verify_blockchain, save_blockchain):
        self.blockchain = blockchain
        self.peers = peers
        self.verify_blockchain = verify_blockchain
        self.save_blockchain = save_blockchain
        self.health = NodeHealth()
        self.last_sync_time = time.time()
        self.sync_failures = 0
        self.max_sync_failures = 5
        
    async def sync_with_peer(self, peer_url: str, timeout: int = 10) -> bool:
        """
        Sync blockchain with a single peer
        Returns True if sync successful
        """
        try:
            url = peer_url.rstrip("/") + "/get_blockchain"
            res = requests.post(url, timeout=timeout)
            
            if res.status_code != 200:
                self.health.mark_failure(peer_url)
                return False
                
            data = res.json()
            their_chain = data.get("blockchain")
            
            if not their_chain:
                self.health.mark_failure(peer_url)
                return False
            
            # Only adopt if their chain is longer AND valid
            if len(their_chain) > len(self.blockchain):
                ok, reason = self.verify_blockchain(their_chain)
                if ok:
                    print(f"[sync] SUCCESS: Adopting longer chain from {peer_url}")
                    print(f"[sync] Old length: {len(self.blockchain)}, New length: {len(their_chain)}")
                    self.blockchain.clear()
                    self.blockchain.extend(their_chain)
                    self.save_blockchain()
                    self.health.mark_success(peer_url)
                    self.last_sync_time = time.time()
                    self.sync_failures = 0
                    return True
                else:
                    print(f"[sync] REJECTED: Invalid chain from {peer_url}: {reason}")
                    self.health.mark_failure(peer_url)
                    return False
            else:
                # Chain is same or shorter, but peer is healthy
                self.health.mark_success(peer_url)
                return False
                
        except Exception as e:
            print(f"[sync] ERROR: Failed to sync with {peer_url}: {e}")
            self.health.mark_failure(peer_url)
            return False
    
    async def sync_with_best_peer(self) -> bool:
        """
        Try to sync with the best available peer
        Returns True if any sync succeeded
        """
        if not self.peers:
            print("[sync] No peers configured - running in standalone mode")
            return False
        
        # Get healthy peers
        healthy_peers = self.health.get_healthy_peers(self.peers)
        
        if not healthy_peers:
            print("[sync] WARNING: No healthy peers available!")
            print("[sync] Attempting peer recovery...")
            self.health.try_recover_peers()
            healthy_peers = self.health.get_healthy_peers(self.peers)
            
            if not healthy_peers:
                print("[sync] CRITICAL: All peers are down!")
                self.sync_failures += 1
                return False
        
        print(f"[sync] Syncing with {len(healthy_peers)} healthy peers...")
        
        # Try each peer
        for peer_url in healthy_peers:
            success = await self.sync_with_peer(peer_url)
            if success:
                return True
        
        print("[sync] No peer had a longer valid chain")
        return False
    
    async def periodic_sync(self, interval_sec: int = 30):
        """
        Periodic sync with automatic failure handling
        """
        await asyncio.sleep(5)  # Initial delay
        
        while True:
            try:
                print(f"\n[sync] === Periodic Sync ({time.strftime('%H:%M:%S')}) ===")
                
                # Try to sync
                await self.sync_with_best_peer()
                
                # Show health stats
                stats = self.health.get_stats()
                print(f"[sync] Network Health: {stats['healthy_peers']} healthy, "
                      f"{stats['degraded_peers']} degraded, {stats['failed_peers']} failed")
                
                # Try to recover failed peers every 5 minutes
                if int(time.time()) % 300 == 0:
                    recovered = self.health.try_recover_peers()
                    if recovered:
                        print(f"[sync] Recovered peers: {recovered}")
                
                # Check if we're in a network partition
                if self.sync_failures >= self.max_sync_failures:
                    print(f"[sync] WARNING: Network partition detected! "
                          f"Failed to sync {self.sync_failures} times")
                    print(f"[sync] Running in isolated mode - continuing with local chain")
                
            except Exception as e:
                print(f"[sync] ERROR in periodic sync: {e}")
            
            await asyncio.sleep(interval_sec)
    
    async def broadcast_block(self, block: dict):
        """
        Broadcast a new block to all healthy peers
        """
        if not self.peers:
            return 0
        
        healthy_peers = self.health.get_healthy_peers(self.peers)
        
        if not healthy_peers:
            print("[gossip] WARNING: No healthy peers to broadcast to!")
            return 0
        
        print(f"[gossip] Broadcasting block #{block['index']} to {len(healthy_peers)} peers...")
        success_count = 0
        
        for peer_url in healthy_peers:
            try:
                url = peer_url.rstrip("/") + "/submit_block"
                res = requests.post(url, json={"block": block}, timeout=5)
                
                if res.status_code == 200:
                    success_count += 1
                    self.health.mark_success(peer_url)
                    print(f"[gossip] SUCCESS: Block sent to {peer_url}")
                else:
                    self.health.mark_failure(peer_url)
                    print(f"[gossip] FAILED: {peer_url} returned {res.status_code}")
                    
            except Exception as e:
                self.health.mark_failure(peer_url)
                print(f"[gossip] ERROR: Failed to send to {peer_url}: {e}")
        
        print(f"[gossip] Broadcast complete: {success_count}/{len(healthy_peers)} peers notified")
        return success_count


# Usage example:
"""
from app.core.network.sync import RobustNodeSync

# Initialize
node_sync = RobustNodeSync(blockchain, peers, verify_blockchain, save_blockchain)

# Start periodic sync
asyncio.create_task(node_sync.periodic_sync(30))

# Broadcast block
await node_sync.broadcast_block(new_block)
"""
