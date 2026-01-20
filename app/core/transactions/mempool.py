"""
PHN Blockchain - Advanced Mempool Management
Features:
- Transaction priority queue by fee (higher fee = higher priority)
- Mempool size limits (prevent spam)
- Transaction expiration (remove old transactions)
- Spam protection
"""

import time
import heapq
from typing import List, Dict, Tuple, Optional


class AdvancedMempool:
    """
    Advanced mempool with priority queue and spam protection
    Transactions with higher fees get priority
    """
    
    def __init__(self, max_size: int = 10000, max_tx_age: int = 3600):
        """
        Initialize advanced mempool
        
        Args:
            max_size: Maximum number of transactions in mempool
            max_tx_age: Maximum age of transaction in seconds (default: 1 hour)
        """
        self.max_size = max_size
        self.max_tx_age = max_tx_age
        
        # Priority queue: (negative_fee, timestamp, txid, transaction)
        # Using negative fee because heapq is min-heap, we want max-heap for fees
        self.priority_queue: List[Tuple[float, float, str, Dict]] = []
        
        # Index for fast lookups
        self.tx_index: Dict[str, Dict] = {}  # txid -> transaction
        
        # Statistics
        self.total_received = 0
        self.total_rejected = 0
        self.total_expired = 0
        
        print(f"[Mempool] Initialized - Max Size: {max_size}, Max Age: {max_tx_age}s")
    
    def add_transaction(self, tx: Dict) -> Tuple[bool, str]:
        """
        Add transaction to mempool with priority
        
        Returns:
            (success, message)
        """
        self.total_received += 1
        
        # Validate transaction structure
        if not self._validate_structure(tx):
            self.total_rejected += 1
            return False, "Invalid transaction structure"
        
        txid = tx.get("txid")
        
        # Check if already in mempool
        if txid in self.tx_index:
            return False, "Transaction already in mempool"
        
        # Check timestamp
        current_time = time.time()
        tx_timestamp = float(tx.get("timestamp", 0))
        
        if current_time - tx_timestamp > self.max_tx_age:
            self.total_rejected += 1
            return False, f"Transaction too old ({current_time - tx_timestamp:.0f}s)"
        
        # Check mempool size limit
        if len(self.priority_queue) >= self.max_size:
            # Remove lowest fee transaction if this one has higher fee
            if self.priority_queue:
                lowest_fee_tx = self.priority_queue[0]
                lowest_fee = -lowest_fee_tx[0]  # Convert back to positive
                new_fee = float(tx.get("fee", 0))
                
                if new_fee <= lowest_fee:
                    self.total_rejected += 1
                    return False, f"Mempool full - fee too low (need > {lowest_fee})"
                
                # Remove lowest fee transaction
                removed = heapq.heappop(self.priority_queue)
                removed_txid = removed[2]
                del self.tx_index[removed_txid]
                print(f"[Mempool] Evicted low-fee tx {removed_txid[:16]}... (fee: {lowest_fee})")
        
        # Add to priority queue
        fee = float(tx.get("fee", 0))
        heapq.heappush(self.priority_queue, (-fee, tx_timestamp, txid, tx))
        self.tx_index[txid] = tx
        
        print(f"[Mempool] Added tx {txid[:16]}... (fee: {fee}, queue size: {len(self.priority_queue)})")
        return True, "Added to mempool"
    
    def get_transactions_for_mining(self, max_count: int = 1000) -> List[Dict]:
        """
        Get transactions for mining, ordered by fee (highest first)
        
        Args:
            max_count: Maximum number of transactions to return
            
        Returns:
            List of transactions sorted by fee (descending)
        """
        # Remove expired transactions first
        self._remove_expired()
        
        # Sort by fee (highest first)
        sorted_txs = sorted(self.priority_queue, key=lambda x: x[0])  # Already negative, so this gives descending
        
        # Return up to max_count transactions
        transactions = [tx[3] for tx in sorted_txs[:max_count]]
        
        print(f"[Mempool] Providing {len(transactions)} transactions for mining (sorted by fee)")
        if transactions:
            highest_fee = float(transactions[0].get("fee", 0))
            lowest_fee = float(transactions[-1].get("fee", 0))
            print(f"[Mempool] Fee range: {highest_fee} (highest) to {lowest_fee} (lowest)")
        
        return transactions
    
    def remove_transaction(self, txid: str) -> bool:
        """
        Remove transaction from mempool (e.g., after it's mined)
        
        Args:
            txid: Transaction ID to remove
            
        Returns:
            True if removed, False if not found
        """
        if txid not in self.tx_index:
            return False
        
        # Remove from index
        del self.tx_index[txid]
        
        # Remove from priority queue
        self.priority_queue = [tx for tx in self.priority_queue if tx[2] != txid]
        heapq.heapify(self.priority_queue)
        
        print(f"[Mempool] Removed tx {txid[:16]}...")
        return True
    
    def remove_transactions(self, txids: List[str]):
        """Remove multiple transactions (e.g., after block is mined)"""
        removed_count = 0
        for txid in txids:
            if self.remove_transaction(txid):
                removed_count += 1
        
        print(f"[Mempool] Removed {removed_count} transactions after block mining")
    
    def _remove_expired(self):
        """Remove transactions that are too old"""
        current_time = time.time()
        expired = []
        
        for neg_fee, timestamp, txid, tx in self.priority_queue:
            if current_time - timestamp > self.max_tx_age:
                expired.append(txid)
        
        if expired:
            for txid in expired:
                self.remove_transaction(txid)
            
            self.total_expired += len(expired)
            print(f"[Mempool] Removed {len(expired)} expired transactions")
    
    def _validate_structure(self, tx: Dict) -> bool:
        """Validate basic transaction structure"""
        required_fields = ["sender", "recipient", "amount", "fee", "timestamp", "txid", "signature"]
        for field in required_fields:
            if field not in tx:
                return False
        return True
    
    def get_size(self) -> int:
        """Get current mempool size"""
        return len(self.priority_queue)
    
    def get_transaction(self, txid: str) -> Optional[Dict]:
        """Get transaction by ID"""
        return self.tx_index.get(txid)
    
    def clear(self):
        """Clear all transactions from mempool"""
        count = len(self.priority_queue)
        self.priority_queue.clear()
        self.tx_index.clear()
        print(f"[Mempool] Cleared {count} transactions")
    
    def get_statistics(self) -> Dict:
        """Get mempool statistics"""
        fees = [float(tx[3].get("fee", 0)) for tx in self.priority_queue]
        
        stats = {
            "current_size": len(self.priority_queue),
            "max_size": self.max_size,
            "utilization": (len(self.priority_queue) / self.max_size * 100) if self.max_size > 0 else 0,
            "total_received": self.total_received,
            "total_rejected": self.total_rejected,
            "total_expired": self.total_expired,
            "avg_fee": sum(fees) / len(fees) if fees else 0,
            "min_fee": min(fees) if fees else 0,
            "max_fee": max(fees) if fees else 0
        }
        
        return stats
    
    def print_statistics(self):
        """Print detailed mempool statistics"""
        stats = self.get_statistics()
        
        print("\n" + "="*70)
        print("MEMPOOL STATISTICS")
        print("="*70)
        print(f"Current Size: {stats['current_size']} / {stats['max_size']}")
        print(f"Utilization: {stats['utilization']:.1f}%")
        print(f"Total Received: {stats['total_received']}")
        print(f"Total Rejected: {stats['total_rejected']}")
        print(f"Total Expired: {stats['total_expired']}")
        print(f"Average Fee: {stats['avg_fee']:.6f} PHN")
        print(f"Min Fee: {stats['min_fee']:.6f} PHN")
        print(f"Max Fee: {stats['max_fee']:.6f} PHN")
        print("="*70 + "\n")


# Global instance
advanced_mempool = AdvancedMempool(max_size=10000, max_tx_age=3600)


if __name__ == "__main__":
    # Test advanced mempool
    print("Testing Advanced Mempool System")
    print("="*70)
    
    # Create test mempool
    mempool = AdvancedMempool(max_size=5, max_tx_age=100)
    
    # Test 1: Add transactions with different fees
    print("\n[Test 1] Add transactions with different fees:")
    test_txs = [
        {"txid": "tx1", "sender": "A", "recipient": "B", "amount": 10, "fee": 0.01, "timestamp": time.time(), "signature": "sig1"},
        {"txid": "tx2", "sender": "C", "recipient": "D", "amount": 20, "fee": 0.05, "timestamp": time.time(), "signature": "sig2"},
        {"txid": "tx3", "sender": "E", "recipient": "F", "amount": 30, "fee": 0.03, "timestamp": time.time(), "signature": "sig3"},
        {"txid": "tx4", "sender": "G", "recipient": "H", "amount": 40, "fee": 0.10, "timestamp": time.time(), "signature": "sig4"},
        {"txid": "tx5", "sender": "I", "recipient": "J", "amount": 50, "fee": 0.02, "timestamp": time.time(), "signature": "sig5"},
    ]
    
    for tx in test_txs:
        success, msg = mempool.add_transaction(tx)
        print(f"  {tx['txid']}: {msg}")
    
    # Test 2: Get transactions for mining (should be sorted by fee)
    print("\n[Test 2] Get transactions for mining (should be sorted by fee):")
    mining_txs = mempool.get_transactions_for_mining()
    print(f"  Order: {[tx['txid'] for tx in mining_txs]}")
    print(f"  Fees: {[tx['fee'] for tx in mining_txs]}")
    
    # Test 3: Add transaction when mempool is full (should evict lowest fee)
    print("\n[Test 3] Add high-fee transaction to full mempool:")
    high_fee_tx = {"txid": "tx6", "sender": "K", "recipient": "L", "amount": 60, "fee": 0.20, "timestamp": time.time(), "signature": "sig6"}
    success, msg = mempool.add_transaction(high_fee_tx)
    print(f"  Result: {msg}")
    
    # Test 4: Add low-fee transaction to full mempool (should be rejected)
    print("\n[Test 4] Add low-fee transaction to full mempool:")
    low_fee_tx = {"txid": "tx7", "sender": "M", "recipient": "N", "amount": 70, "fee": 0.001, "timestamp": time.time(), "signature": "sig7"}
    success, msg = mempool.add_transaction(low_fee_tx)
    print(f"  Result: {msg}")
    
    # Test 5: Statistics
    print("\n[Test 5] Mempool statistics:")
    mempool.print_statistics()
    
    print("="*70)
    print("All tests completed!")
