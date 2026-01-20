"""
PHN Blockchain - Explorer API Endpoints
Query blocks, search blockchain, network statistics
"""

from aiohttp import web
import time
from app.core.blockchain.chain import blockchain, pending_txs, get_balance, calculate_total_mined, get_current_block_reward
from app.core.consensus.difficulty import DifficultyAdjuster
from app.core.config import settings

routes = web.RouteTableDef()

# Initialize difficulty adjuster for stats
difficulty_adjuster = DifficultyAdjuster(target_block_time=60, adjustment_interval=10)


def standard_response(success: bool, data=None, error=None):
    """Standard API response format"""
    return {
        "success": success,
        "data": data,
        "error": error,
        "timestamp": int(time.time())
    }


@routes.get("/api/v1/explorer/block/{index}")
async def get_block_by_index(request):
    """
    Get block by index
    
    Path:
        - index: Block index (0 = genesis)
    
    Returns:
        - block: Complete block data
    """
    try:
        index = int(request.match_info['index'])
        
        if index < 0 or index >= len(blockchain):
            return web.json_response(
                standard_response(success=False, error="Block not found"),
                status=404
            )
        
        block = blockchain[index]
        
        # Enrich block data
        enriched_block = {
            **block,
            "transaction_count": len(block.get("transactions", [])),
            "total_amount": sum(float(tx.get("amount", 0)) for tx in block.get("transactions", [])),
            "total_fees": sum(float(tx.get("fee", 0)) for tx in block.get("transactions", [])),
            "size_bytes": len(str(block).encode()),
            "confirmations": len(blockchain) - index
        }
        
        return web.json_response(standard_response(
            success=True,
            data=enriched_block
        ))
    
    except ValueError:
        return web.json_response(
            standard_response(success=False, error="Invalid block index"),
            status=400
        )
    except Exception as e:
        return web.json_response(
            standard_response(success=False, error=str(e)),
            status=500
        )


@routes.get("/api/v1/explorer/blocks/latest")
async def get_latest_blocks(request):
    """
    Get latest blocks
    
    Query params:
        - limit: Number of blocks (default 10, max 100)
    
    Returns:
        - blocks: List of recent blocks
    """
    try:
        limit = min(int(request.query.get('limit', 10)), 100)
        
        if len(blockchain) == 0:
            return web.json_response(standard_response(
                success=True,
                data={"blocks": [], "total": 0}
            ))
        
        # Get latest blocks
        start_index = max(0, len(blockchain) - limit)
        latest_blocks = []
        
        for i in range(len(blockchain) - 1, start_index - 1, -1):
            block = blockchain[i]
            latest_blocks.append({
                "index": block.get("index"),
                "hash": block.get("hash"),
                "timestamp": block.get("timestamp"),
                "transaction_count": len(block.get("transactions", [])),
                "total_amount": sum(float(tx.get("amount", 0)) for tx in block.get("transactions", [])),
                "confirmations": len(blockchain) - i
            })
        
        return web.json_response(standard_response(
            success=True,
            data={
                "blocks": latest_blocks,
                "total": len(latest_blocks),
                "chain_height": len(blockchain)
            }
        ))
    
    except Exception as e:
        return web.json_response(
            standard_response(success=False, error=str(e)),
            status=500
        )


@routes.get("/api/v1/explorer/blocks/range/{start}/{end}")
async def get_block_range(request):
    """
    Get range of blocks
    
    Path:
        - start: Start block index
        - end: End block index (inclusive)
    
    Returns:
        - blocks: List of blocks in range
    """
    try:
        start = int(request.match_info['start'])
        end = int(request.match_info['end'])
        
        if start < 0 or end >= len(blockchain) or start > end:
            return web.json_response(
                standard_response(success=False, error="Invalid block range"),
                status=400
            )
        
        if end - start > 100:
            return web.json_response(
                standard_response(success=False, error="Range too large (max 100 blocks)"),
                status=400
            )
        
        blocks = []
        for i in range(start, end + 1):
            block = blockchain[i]
            blocks.append({
                "index": block.get("index"),
                "hash": block.get("hash"),
                "timestamp": block.get("timestamp"),
                "transaction_count": len(block.get("transactions", [])),
                "total_amount": sum(float(tx.get("amount", 0)) for tx in block.get("transactions", [])),
                "nonce": block.get("nonce"),
                "prev_hash": block.get("prev_hash")
            })
        
        return web.json_response(standard_response(
            success=True,
            data={
                "blocks": blocks,
                "start": start,
                "end": end,
                "count": len(blocks)
            }
        ))
    
    except ValueError:
        return web.json_response(
            standard_response(success=False, error="Invalid block indices"),
            status=400
        )
    except Exception as e:
        return web.json_response(
            standard_response(success=False, error=str(e)),
            status=500
        )


@routes.get("/api/v1/explorer/stats")
async def get_network_stats(request):
    """
    Get comprehensive network statistics
    
    Returns:
        - Network stats including blocks, transactions, supply, etc.
    """
    try:
        # Calculate comprehensive stats
        total_blocks = len(blockchain)
        total_mined = calculate_total_mined()
        current_reward = get_current_block_reward()
        
        # Transaction stats
        total_transactions = sum(len(block.get("transactions", [])) for block in blockchain)
        total_transactions += len(pending_txs)
        
        # Calculate total fees
        total_fees = 0.0
        for block in blockchain:
            for tx in block.get("transactions", []):
                if tx.get("sender") not in ["coinbase", "miners_pool"]:
                    total_fees += float(tx.get("fee", 0))
        
        # Calculate average block time
        if len(blockchain) > 1:
            time_span = blockchain[-1].get("timestamp") - blockchain[0].get("timestamp")
            avg_block_time = time_span / (len(blockchain) - 1)
        else:
            avg_block_time = 0
        
        # Count unique addresses
        unique_addresses = set()
        for block in blockchain:
            for tx in block.get("transactions", []):
                sender = tx.get("sender")
                recipient = tx.get("recipient")
                if sender and sender not in ["coinbase", "miners_pool"]:
                    unique_addresses.add(sender)
                if recipient:
                    unique_addresses.add(recipient)
        
        # Calculate difficulty
        current_difficulty = difficulty_adjuster.calculate_difficulty(blockchain)
        
        # Calculate chain size
        chain_size = sum(len(str(block).encode()) for block in blockchain)
        
        return web.json_response(standard_response(
            success=True,
            data={
                "chain": {
                    "height": total_blocks,
                    "size_bytes": chain_size,
                    "size_mb": round(chain_size / (1024 * 1024), 2)
                },
                "supply": {
                    "total_supply": settings.TOTAL_SUPPLY,
                    "circulating_supply": total_mined,
                    "remaining": settings.TOTAL_SUPPLY - total_mined,
                    "percentage_mined": round(total_mined / settings.TOTAL_SUPPLY * 100, 2)
                },
                "mining": {
                    "current_difficulty": current_difficulty,
                    "current_block_reward": current_reward,
                    "average_block_time": round(avg_block_time, 2),
                    "target_block_time": 60,
                    "total_blocks_mined": total_blocks
                },
                "transactions": {
                    "total_confirmed": total_transactions - len(pending_txs),
                    "pending": len(pending_txs),
                    "total_fees_paid": total_fees
                },
                "network": {
                    "unique_addresses": len(unique_addresses),
                    "active_addresses_24h": _count_active_addresses(86400)
                },
                "timestamp": int(time.time())
            }
        ))
    
    except Exception as e:
        return web.json_response(
            standard_response(success=False, error=str(e)),
            status=500
        )


@routes.get("/api/v1/explorer/search/{query}")
async def search_blockchain(request):
    """
    Search blockchain by block hash, txid, or address
    
    Path:
        - query: Search query (block hash, txid, or address)
    
    Returns:
        - type: Type of result (block, transaction, address)
        - data: Result data
    """
    try:
        query = request.match_info['query'].strip()
        
        # Try to find block by hash
        for block in blockchain:
            if block.get("hash") == query:
                return web.json_response(standard_response(
                    success=True,
                    data={
                        "type": "block",
                        "result": block
                    }
                ))
        
        # Try to find transaction by txid
        for block in blockchain:
            for tx in block.get("transactions", []):
                if tx.get("txid") == query:
                    return web.json_response(standard_response(
                        success=True,
                        data={
                            "type": "transaction",
                            "result": tx,
                            "block_index": block.get("index"),
                            "confirmations": len(blockchain) - block.get("index")
                        }
                    ))
        
        # Check pending transactions
        for tx in pending_txs:
            if tx.get("txid") == query:
                return web.json_response(standard_response(
                    success=True,
                    data={
                        "type": "transaction",
                        "result": tx,
                        "block_index": None,
                        "status": "pending"
                    }
                ))
        
        # Try as address
        balance = get_balance(query)
        if balance > 0 or _address_exists(query):
            # Get transaction history
            transactions = []
            for block in blockchain:
                for tx in block.get("transactions", []):
                    if tx.get("sender") == query or tx.get("recipient") == query:
                        transactions.append({
                            "txid": tx.get("txid"),
                            "block": block.get("index"),
                            "timestamp": block.get("timestamp"),
                            "type": "sent" if tx.get("sender") == query else "received",
                            "amount": tx.get("amount")
                        })
            
            return web.json_response(standard_response(
                success=True,
                data={
                    "type": "address",
                    "result": {
                        "address": query,
                        "balance": balance,
                        "transaction_count": len(transactions),
                        "transactions": transactions[-10:]  # Last 10 transactions
                    }
                }
            ))
        
        return web.json_response(
            standard_response(success=False, error="No results found"),
            status=404
        )
    
    except Exception as e:
        return web.json_response(
            standard_response(success=False, error=str(e)),
            status=500
        )


@routes.get("/api/v1/explorer/info")
async def get_node_info(request):
    """
    Get node information
    
    Returns:
        - Node and blockchain information
    """
    try:
        return web.json_response(standard_response(
            success=True,
            data={
                "node": {
                    "version": settings.NODE_VERSION,
                    "network": "PHN Mainnet"
                },
                "blockchain": {
                    "height": len(blockchain),
                    "best_block_hash": blockchain[-1].get("hash") if blockchain else None,
                    "difficulty": difficulty_adjuster.calculate_difficulty(blockchain),
                    "total_supply": settings.TOTAL_SUPPLY,
                    "circulating_supply": calculate_total_mined()
                },
                "mempool": {
                    "size": len(pending_txs),
                    "total_fee": sum(float(tx.get("fee", 0)) for tx in pending_txs)
                },
                "endpoints": {
                    "explorer": "/api/v1/explorer/*",
                    "balance": "/api/v1/balance/*",
                    "transactions": "/api/v1/tx/*"
                }
            }
        ))
    
    except Exception as e:
        return web.json_response(
            standard_response(success=False, error=str(e)),
            status=500
        )


def _count_active_addresses(time_window: int) -> int:
    """Count addresses active in time window (seconds)"""
    current_time = time.time()
    active = set()
    
    for block in reversed(blockchain):
        if current_time - block.get("timestamp", 0) > time_window:
            break
        
        for tx in block.get("transactions", []):
            sender = tx.get("sender")
            recipient = tx.get("recipient")
            if sender and sender not in ["coinbase", "miners_pool"]:
                active.add(sender)
            if recipient:
                active.add(recipient)
    
    return len(active)


def _address_exists(address: str) -> bool:
    """Check if address has any transactions"""
    for block in blockchain:
        for tx in block.get("transactions", []):
            if tx.get("sender") == address or tx.get("recipient") == address:
                return True
    return False
