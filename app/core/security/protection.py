"""
PHN Blockchain - 51% Attack Mitigation System
Implements checkpointing and reorganization alerts to detect potential attacks
"""

import time
from typing import List, Dict, Optional

class ChainProtection:
    """
    Protects against 51% attacks with checkpointing and deep reorg detection
    """
    
    def __init__(self, checkpoint_interval: int = 100, max_reorg_depth: int = 10):
        """
        Initialize chain protection
        
        Args:
            checkpoint_interval: Create checkpoint every N blocks
            max_reorg_depth: Max allowed chain reorganization depth
        """
        self.checkpoint_interval = checkpoint_interval
        self.max_reorg_depth = max_reorg_depth
        self.checkpoints: Dict[int, str] = {}  # block_index -> block_hash
        self.reorg_attempts = []  # Track reorganization attempts
        
        print(f"[SECURITY] Chain Protection initialized")
        print(f"[SECURITY] Checkpoint interval: {checkpoint_interval} blocks")
        print(f"[SECURITY] Max reorg depth: {max_reorg_depth} blocks")
    
    def create_checkpoint(self, block_index: int, block_hash: str):
        """
        Create a checkpoint at specific block height
        Checkpointed blocks cannot be reorganized
        """
        if block_index % self.checkpoint_interval == 0:
            self.checkpoints[block_index] = block_hash
            print(f"[CHECKPOINT] Block #{block_index} - {block_hash[:16]}...")
            return True
        return False
    
    def is_checkpointed(self, block_index: int) -> bool:
        """Check if block is checkpointed"""
        return block_index in self.checkpoints
    
    def get_checkpoint(self, block_index: int) -> Optional[str]:
        """Get checkpoint hash for block"""
        return self.checkpoints.get(block_index)
    
    def validate_chain_against_checkpoints(self, blockchain: List[Dict]) -> tuple[bool, str]:
        """
        Validate blockchain against checkpoints
        SECURITY: Prevents deep chain reorganization attacks
        """
        for index, expected_hash in self.checkpoints.items():
            if index < len(blockchain):
                block = blockchain[index]
                if block is None:
                    continue
                    
                actual_hash = block.get("hash")
                
                if actual_hash != expected_hash:
                    error_msg = (
                        f"[SECURITY ALERT] Checkpoint violation at block #{index}\n"
                        f"Expected: {expected_hash[:16]}...\n"
                        f"Got:      {actual_hash[:16] if actual_hash else 'None'}...\n"
                        f"POSSIBLE 51% ATTACK DETECTED!"
                    )
                    print(error_msg)
                    return False, error_msg
        
        return True, "Chain valid against checkpoints"
    
    def detect_deep_reorg(self, old_chain_length: int, new_chain_length: int, 
                          common_ancestor: int) -> tuple[bool, str]:
        """
        Detect deep reorganization attempts
        SECURITY: Alert on suspicious chain replacements
        """
        reorg_depth = old_chain_length - common_ancestor
        
        if reorg_depth > self.max_reorg_depth:
            alert_msg = (
                f"\n{'='*70}\n"
                f"[SECURITY ALERT] DEEP CHAIN REORGANIZATION DETECTED!\n"
                f"{'='*70}\n"
                f"Reorganization depth: {reorg_depth} blocks\n"
                f"Maximum allowed: {self.max_reorg_depth} blocks\n"
                f"Old chain length: {old_chain_length}\n"
                f"New chain length: {new_chain_length}\n"
                f"Common ancestor: Block #{common_ancestor}\n"
                f"{'='*70}\n"
                f"POSSIBLE 51% ATTACK IN PROGRESS!\n"
                f"Action: Rejecting chain reorganization\n"
                f"{'='*70}\n"
            )
            
            # Log the attempt
            self.reorg_attempts.append({
                "timestamp": time.time(),
                "depth": reorg_depth,
                "old_length": old_chain_length,
                "new_length": new_chain_length,
                "common_ancestor": common_ancestor
            })
            
            print(alert_msg)
            return True, alert_msg
        
        return False, f"Reorganization depth {reorg_depth} is acceptable"
    
    def auto_checkpoint_new_block(self, blockchain: List[Dict]) -> bool:
        """
        Automatically create checkpoint for new blocks
        Called after each new block is added
        """
        if not blockchain:
            return False
        
        latest_block = blockchain[-1]
        block_index = latest_block.get("index", 0)
        block_hash = latest_block.get("hash", "")
        
        return self.create_checkpoint(block_index, block_hash)
    
    def get_security_stats(self) -> Dict:
        """Get security statistics"""
        return {
            "total_checkpoints": len(self.checkpoints),
            "checkpoint_interval": self.checkpoint_interval,
            "max_reorg_depth": self.max_reorg_depth,
            "reorg_attempts_blocked": len(self.reorg_attempts),
            "last_checkpoint_block": max(self.checkpoints.keys()) if self.checkpoints else 0
        }
    
    def print_security_report(self):
        """Print security report"""
        stats = self.get_security_stats()
        
        print("\n" + "="*70)
        print("CHAIN PROTECTION SECURITY REPORT")
        print("="*70)
        print(f"Total Checkpoints: {stats['total_checkpoints']}")
        print(f"Checkpoint Interval: Every {stats['checkpoint_interval']} blocks")
        print(f"Max Reorg Depth: {stats['max_reorg_depth']} blocks")
        print(f"Reorg Attempts Blocked: {stats['reorg_attempts_blocked']}")
        print(f"Last Checkpoint: Block #{stats['last_checkpoint_block']}")
        
        if self.reorg_attempts:
            print("\n[SECURITY] Recent Attack Attempts:")
            for i, attempt in enumerate(self.reorg_attempts[-5:], 1):
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(attempt['timestamp']))
                print(f"  {i}. Depth: {attempt['depth']} blocks - {timestamp}")
        
        print("="*70 + "\n")


# Global instance
chain_protection = ChainProtection(
    checkpoint_interval=100,  # Checkpoint every 100 blocks
    max_reorg_depth=10        # Max 10 blocks reorganization
)


if __name__ == "__main__":
    # Test chain protection
    print("Testing Chain Protection System")
    print("="*70)
    
    protection = ChainProtection(checkpoint_interval=5, max_reorg_depth=3)
    
    # Simulate blockchain
    test_chain = []
    for i in range(15):
        block = {
            "index": i,
            "hash": f"hash_{i}_{'0'*60}",
            "timestamp": time.time(),
            "transactions": []
        }
        test_chain.append(block)
        
        # Auto checkpoint
        if protection.auto_checkpoint_new_block(test_chain):
            print(f"  Block #{i} checkpointed")
    
    print("\n[Test 1] Validate chain against checkpoints:")
    valid, msg = protection.validate_chain_against_checkpoints(test_chain)
    print(f"  Result: {valid} - {msg}")
    
    print("\n[Test 2] Detect shallow reorg (2 blocks):")
    is_attack, msg = protection.detect_deep_reorg(15, 16, 13)
    print(f"  Attack detected: {is_attack}")
    
    print("\n[Test 3] Detect deep reorg (10 blocks - ATTACK):")
    is_attack, msg = protection.detect_deep_reorg(15, 20, 5)
    print(f"  Attack detected: {is_attack}")
    
    # Print report
    protection.print_security_report()
    
    print("="*70)
    print("All tests completed!")
