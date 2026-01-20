"""
PHN Blockchain - Balance API Endpoints
Query PHN balances, assets, and token holdings
"""

from aiohttp import web
import time
from app.core.blockchain.chain import blockchain, get_balance, pending_txs

routes = web.RouteTableDef()


def standard_response(success: bool, data=None, error=None):
    """Standard API response format"""
    return {
        "success": success,
        "data": data,
        "error": error,
        "timestamp": int(time.time())
    }


@routes.get("/api/v1/balance/{address}")
async def get_phn_balance(request):
    """
    Get PHN balance for an address
    
    Path:
        - address: PHN address
    
    Returns:
        - balance: Current PHN balance
        - pending: Pending balance from mempool
    """
    try:
        address = request.match_info['address']
        
        # Get confirmed balance
        balance = get_balance(address)
        
        # Calculate pending balance from unconfirmed transactions
        pending_balance = 0.0
        for tx in pending_txs:
            if tx.get("recipient") == address:
                pending_balance += float(tx.get("amount", 0))
            if tx.get("sender") == address:
                pending_balance -= (float(tx.get("amount", 0)) + float(tx.get("fee", 0)))
        
        return web.json_response(standard_response(
            success=True,
            data={
                "address": address,
                "balance": balance,
                "pending": pending_balance,
                "total": balance + pending_balance
            }
        ))
    
    except Exception as e:
        return web.json_response(
            standard_response(success=False, error=str(e)),
            status=500
        )


@routes.get("/api/v1/balance/portfolio/{address}")
async def get_portfolio(request):
    """
    Get complete portfolio for an address (PHN + assets)
    
    Path:
        - address: PHN address
    
    Returns:
        - phn_balance: PHN token balance
        - assets: List of owned assets
        - transactions: Recent transaction count
    """
    try:
        address = request.match_info['address']
        
        # Get PHN balance
        balance = get_balance(address)
        
        # Count transactions
        tx_count = 0
        for block in blockchain:
            for tx in block.get("transactions", []):
                if tx.get("sender") == address or tx.get("recipient") == address:
                    tx_count += 1
        
        # Get received and sent amounts
        total_received = 0.0
        total_sent = 0.0
        for block in blockchain:
            for tx in block.get("transactions", []):
                if tx.get("recipient") == address:
                    total_received += float(tx.get("amount", 0))
                if tx.get("sender") == address:
                    total_sent += float(tx.get("amount", 0)) + float(tx.get("fee", 0))
        
        return web.json_response(standard_response(
            success=True,
            data={
                "address": address,
                "phn_balance": balance,
                "total_received": total_received,
                "total_sent": total_sent,
                "transaction_count": tx_count,
                "first_seen": _get_first_seen(address),
                "last_activity": _get_last_activity(address)
            }
        ))
    
    except Exception as e:
        return web.json_response(
            standard_response(success=False, error=str(e)),
            status=500
        )


@routes.get("/api/v1/balance/history/{address}")
async def get_balance_history(request):
    """
    Get balance history over time
    
    Path:
        - address: PHN address
    
    Query params:
        - limit: Number of data points (default 100)
    
    Returns:
        - history: List of balance snapshots
    """
    try:
        address = request.match_info['address']
        limit = int(request.query.get('limit', 100))
        
        # Calculate balance at each block
        balance_history = []
        running_balance = 0.0
        
        for block in blockchain:
            block_change = 0.0
            
            for tx in block.get("transactions", []):
                if tx.get("recipient") == address:
                    block_change += float(tx.get("amount", 0))
                if tx.get("sender") == address:
                    block_change -= (float(tx.get("amount", 0)) + float(tx.get("fee", 0)))
            
            if block_change != 0:  # Only record blocks with balance changes
                running_balance += block_change
                balance_history.append({
                    "block": block.get("index"),
                    "timestamp": block.get("timestamp"),
                    "balance": running_balance,
                    "change": block_change
                })
        
        # Limit results
        if len(balance_history) > limit:
            # Sample evenly
            step = len(balance_history) // limit
            balance_history = balance_history[::step][:limit]
        
        return web.json_response(standard_response(
            success=True,
            data={
                "address": address,
                "current_balance": running_balance,
                "history": balance_history,
                "data_points": len(balance_history)
            }
        ))
    
    except Exception as e:
        return web.json_response(
            standard_response(success=False, error=str(e)),
            status=500
        )


@routes.get("/api/v1/balance/richlist")
async def get_richlist(request):
    """
    Get richest addresses
    
    Query params:
        - limit: Number of addresses (default 100)
        - exclude_system: Exclude system addresses (default true)
    
    Returns:
        - addresses: List of addresses with balances
    """
    try:
        limit = int(request.query.get('limit', 100))
        exclude_system = request.query.get('exclude_system', 'true').lower() == 'true'
        
        # Calculate all balances
        balances = {}
        
        for block in blockchain:
            for tx in block.get("transactions", []):
                recipient = tx.get("recipient")
                sender = tx.get("sender")
                
                # Skip system addresses if requested
                if exclude_system and sender in ["coinbase", "miners_pool"]:
                    continue
                
                if recipient:
                    balances[recipient] = balances.get(recipient, 0.0) + float(tx.get("amount", 0))
                
                if sender and sender not in ["coinbase", "miners_pool"]:
                    balances[sender] = balances.get(sender, 0.0) - (float(tx.get("amount", 0)) + float(tx.get("fee", 0)))
        
        # Sort by balance
        sorted_addresses = sorted(
            [{"address": addr, "balance": bal} for addr, bal in balances.items() if bal > 0],
            key=lambda x: x["balance"],
            reverse=True
        )[:limit]
        
        # Calculate stats
        total_supply = sum(bal for bal in balances.values() if bal > 0)
        
        return web.json_response(standard_response(
            success=True,
            data={
                "addresses": sorted_addresses,
                "total_addresses": len([bal for bal in balances.values() if bal > 0]),
                "total_supply": total_supply,
                "top_100_percentage": sum(a["balance"] for a in sorted_addresses[:100]) / total_supply * 100 if total_supply > 0 else 0
            }
        ))
    
    except Exception as e:
        return web.json_response(
            standard_response(success=False, error=str(e)),
            status=500
        )


def _get_first_seen(address: str) -> int:
    """Get timestamp of first transaction"""
    for block in blockchain:
        for tx in block.get("transactions", []):
            if tx.get("sender") == address or tx.get("recipient") == address:
                return int(block.get("timestamp", 0))
    return 0


def _get_last_activity(address: str) -> int:
    """Get timestamp of last transaction"""
    last = 0
    for block in blockchain:
        for tx in block.get("transactions", []):
            if tx.get("sender") == address or tx.get("recipient") == address:
                last = int(block.get("timestamp", 0))
    return last
