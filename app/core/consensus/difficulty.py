"""
PHN Blockchain - Dynamic Difficulty Adjustment
Automatically adjusts mining difficulty based on block time
Target: 1 block every 60 seconds (configurable)
"""

import time
from typing import List, Dict

class DifficultyAdjuster:
    """
    Dynamic difficulty adjustment algorithm
    Similar to Bitcoin but with faster adjustment
    """
    
    def __init__(self, target_block_time: int = 60, adjustment_interval: int = 10):
        """
        Initialize difficulty adjuster
        
        Args:
            target_block_time: Target time between blocks in seconds (default: 60s)
            adjustment_interval: Number of blocks before adjusting difficulty (default: 10)
        """
        self.target_block_time = target_block_time
        self.adjustment_interval = adjustment_interval
        self.min_difficulty = 1
        self.max_difficulty = 10
    
    def calculate_difficulty(self, blockchain: List[Dict]) -> int:
        """
        Calculate current difficulty based on recent block times
        
        Args:
            blockchain: Full blockchain
            
        Returns:
            New difficulty level (1-10)
        """
        # Genesis block or very few blocks - use default difficulty
        if len(blockchain) <= 1:
            return 3  # Starting difficulty
        
        # Not enough blocks for adjustment yet
        if len(blockchain) < self.adjustment_interval:
            # Get current difficulty from last block
            return self._get_current_difficulty(blockchain)
        
        # Check if we should adjust (every N blocks)
        if len(blockchain) % self.adjustment_interval != 0:
            return self._get_current_difficulty(blockchain)
        
        # Calculate actual time taken for last N blocks
        recent_blocks = blockchain[-self.adjustment_interval:]
        time_taken = recent_blocks[-1]["timestamp"] - recent_blocks[0]["timestamp"]
        
        # Expected time for N blocks
        expected_time = self.target_block_time * self.adjustment_interval
        
        # Calculate adjustment ratio
        adjustment_ratio = expected_time / time_taken if time_taken > 0 else 1.0
        
        # Get current difficulty
        current_difficulty = self._get_current_difficulty(blockchain)
        
        # Adjust difficulty
        if adjustment_ratio > 1.5:  # Blocks too slow
            new_difficulty = max(self.min_difficulty, current_difficulty - 1)
            print(f"[Difficulty] Blocks too slow ({time_taken:.1f}s vs {expected_time}s) - DECREASING difficulty: {current_difficulty} -> {new_difficulty}")
        elif adjustment_ratio < 0.67:  # Blocks too fast
            new_difficulty = min(self.max_difficulty, current_difficulty + 1)
            print(f"[Difficulty] Blocks too fast ({time_taken:.1f}s vs {expected_time}s) - INCREASING difficulty: {current_difficulty} -> {new_difficulty}")
        else:  # Just right
            new_difficulty = current_difficulty
            print(f"[Difficulty] Block time optimal ({time_taken:.1f}s vs {expected_time}s) - MAINTAINING difficulty: {current_difficulty}")
        
        return new_difficulty
    
    def _get_current_difficulty(self, blockchain: List[Dict]) -> int:
        """
        Extract current difficulty from blockchain
        Difficulty is determined by number of leading zeros in hash
        """
        if not blockchain:
            return 3  # Default
        
        # Get last block hash
        last_hash = blockchain[-1].get("hash", "")
        
        # Count leading zeros
        difficulty = 0
        for char in last_hash:
            if char == '0':
                difficulty += 1
            else:
                break
        
        # Ensure within bounds
        return max(self.min_difficulty, min(self.max_difficulty, difficulty))
    
    def get_block_time_stats(self, blockchain: List[Dict], last_n_blocks: int = 100) -> Dict:
        """
        Get statistics about recent block times
        
        Args:
            blockchain: Full blockchain
            last_n_blocks: Number of recent blocks to analyze
            
        Returns:
            Dictionary with statistics
        """
        if len(blockchain) <= 1:
            return {
                "average_block_time": 0,
                "min_block_time": 0,
                "max_block_time": 0,
                "total_blocks": 0
            }
        
        # Get recent blocks
        recent_blocks = blockchain[-min(last_n_blocks, len(blockchain)):]
        
        # Calculate block times
        block_times = []
        for i in range(1, len(recent_blocks)):
            time_diff = recent_blocks[i]["timestamp"] - recent_blocks[i-1]["timestamp"]
            block_times.append(time_diff)
        
        if not block_times:
            return {
                "average_block_time": 0,
                "min_block_time": 0,
                "max_block_time": 0,
                "total_blocks": 0
            }
        
        return {
            "average_block_time": sum(block_times) / len(block_times),
            "min_block_time": min(block_times),
            "max_block_time": max(block_times),
            "total_blocks": len(block_times),
            "target_block_time": self.target_block_time
        }
    
    def print_difficulty_report(self, blockchain: List[Dict]):
        """Print detailed difficulty adjustment report"""
        print("\n" + "="*70)
        print("DIFFICULTY ADJUSTMENT REPORT")
        print("="*70)
        
        current_diff = self._get_current_difficulty(blockchain)
        stats = self.get_block_time_stats(blockchain)
        
        print(f"Current Difficulty: {current_diff}")
        print(f"Target Block Time: {self.target_block_time}s")
        print(f"Average Block Time (last {stats['total_blocks']} blocks): {stats['average_block_time']:.1f}s")
        print(f"Min Block Time: {stats['min_block_time']:.1f}s")
        print(f"Max Block Time: {stats['max_block_time']:.1f}s")
        
        # Calculate performance
        if stats['average_block_time'] > 0:
            performance = (self.target_block_time / stats['average_block_time']) * 100
            print(f"Performance: {performance:.1f}% of target")
        
        # Next adjustment
        blocks_until_adjustment = self.adjustment_interval - (len(blockchain) % self.adjustment_interval)
        print(f"Next adjustment in: {blocks_until_adjustment} blocks")
        
        print("="*70 + "\n")


# Global instance
difficulty_adjuster = DifficultyAdjuster(target_block_time=60, adjustment_interval=10)


def get_current_difficulty(blockchain: List[Dict]) -> int:
    """
    Get current mining difficulty
    Uses dynamic adjustment based on block times
    """
    return difficulty_adjuster.calculate_difficulty(blockchain)


def get_difficulty_stats(blockchain: List[Dict]) -> Dict:
    """Get difficulty statistics"""
    return difficulty_adjuster.get_block_time_stats(blockchain)


if __name__ == "__main__":
    # Test difficulty adjustment
    print("Testing Dynamic Difficulty Adjustment")
    print("="*70)
    
    # Simulate blockchain with varying block times
    test_blockchain = [{"hash": "000genesis", "timestamp": 1000}]
    
    # Add blocks that are too fast (should increase difficulty)
    print("\n[Test 1] Blocks too fast (30s each):")
    for i in range(10):
        block = {
            "hash": "00" + str(i) * 62,  # Difficulty 2
            "timestamp": test_blockchain[-1]["timestamp"] + 30  # Too fast!
        }
        test_blockchain.append(block)
    
    diff1 = difficulty_adjuster.calculate_difficulty(test_blockchain)
    print(f"Result: Difficulty should INCREASE. New difficulty: {diff1}")
    
    # Add blocks that are too slow (should decrease difficulty)
    print("\n[Test 2] Blocks too slow (120s each):")
    test_blockchain2 = [{"hash": "0000start", "timestamp": 2000}]
    for i in range(10):
        block = {
            "hash": "0000" + str(i) * 60,  # Difficulty 4
            "timestamp": test_blockchain2[-1]["timestamp"] + 120  # Too slow!
        }
        test_blockchain2.append(block)
    
    diff2 = difficulty_adjuster.calculate_difficulty(test_blockchain2)
    print(f"Result: Difficulty should DECREASE. New difficulty: {diff2}")
    
    # Perfect timing
    print("\n[Test 3] Perfect timing (60s each):")
    test_blockchain3 = [{"hash": "000perfect", "timestamp": 3000}]
    for i in range(10):
        block = {
            "hash": "000" + str(i) * 61,  # Difficulty 3
            "timestamp": test_blockchain3[-1]["timestamp"] + 60  # Perfect!
        }
        test_blockchain3.append(block)
    
    diff3 = difficulty_adjuster.calculate_difficulty(test_blockchain3)
    print(f"Result: Difficulty should MAINTAIN. New difficulty: {diff3}")
    
    print("\n" + "="*70)
    print("All tests completed!")
