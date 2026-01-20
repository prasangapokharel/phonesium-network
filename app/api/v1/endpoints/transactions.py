"""
PHN Blockchain - Transaction API Endpoints
Send transactions, query history, broadcast signed transactions
"""

from aiohttp import web
import time
from app.core.blockchain.chain import blockchain, pending_txs, get_balance, validate_transaction, public_key_to_address

routes = web.RouteTableDef()


def standard_response(success: bool, data=None, error=None):
    """Standard API response format"""
    return {
        "success": success,
        "data": data,
        "error": error,
        "timestamp": int(time.time())
    }


@routes.post("/api/v1/tx/send")
async def send_transaction(request):
    """
    Send a transaction to the network
    
    Body:
        - tx: Complete transaction object with signature
    
    Returns:
        - txid: Transaction ID
        - status: Transaction status
    """
    try:
        data = await request.json()
        tx = data.get("tx")
        
        if not tx:
            return web.json_response(
                standard_response(success=False, error="tx missing"),
                status=400
            )
        
        # Get sender - could be public key or PHN address
        sender = tx.get("sender")
        if not sender:
            return web.json_response(
                standard_response(success=False, error="sender missing"),
                status=400
            )
        
        # For balance checking, if sender is a public key, convert to PHN address
        if len(sender) == 128:  # Public key format
            balance_address = public_key_to_address(sender)
        else:
            balance_address = sender
        
        # Check balance
        sender_balance = get_balance(balance_address)
        total_needed = float(tx.get("amount", 0)) + float(tx.get("fee", 0))
        
        if sender_balance < total_needed:
            return web.json_response(
                standard_response(
                    success=False,
                    error=f"Insufficient balance. Need {total_needed}, have {sender_balance}"
                ),
                status=400
            )
        
        # Validate transaction
        ok, msg = validate_transaction(tx)
        if not ok:
            return web.json_response(
                standard_response(success=False, error=msg),
                status=400
            )
        
        # Check if already pending
        if any(t["txid"] == tx["txid"] for t in pending_txs):
            return web.json_response(
                standard_response(success=False, error="Transaction already pending"),
                status=400
            )
        
        # Add to mempool
        pending_txs.append(tx)
        
        return web.json_response(standard_response(
            success=True,
            data={
                "txid": tx["txid"],
                "status": "pending",
                "mempool_size": len(pending_txs)
            }
        ))
    
    except Exception as e:
        return web.json_response(
            standard_response(success=False, error=str(e)),
            status=500
        )


@routes.get("/api/v1/tx/{txid}")
async def get_transaction(request):
    """
    Get transaction by TXID
    
    Path:
        - txid: Transaction ID
    
    Returns:
        - transaction: Complete transaction data
        - block_index: Block containing transaction (null if pending)
        - confirmations: Number of confirmations
    """
    try:
        txid = request.match_info['txid']
        
        # Search confirmed transactions
        for block in blockchain:
            for tx in block.get("transactions", []):
                if tx.get("txid") == txid:
                    confirmations = len(blockchain) - block.get("index")
                    return web.json_response(standard_response(
                        success=True,
                        data={
                            "transaction": tx,
                            "block_index": block.get("index"),
                            "block_hash": block.get("hash"),
                            "timestamp": block.get("timestamp"),
                            "confirmations": confirmations,
                            "status": "confirmed"
                        }
                    ))
        
        # Search pending transactions
        for tx in pending_txs:
            if tx.get("txid") == txid:
                return web.json_response(standard_response(
                    success=True,
                    data={
                        "transaction": tx,
                        "block_index": None,
                        "confirmations": 0,
                        "status": "pending"
                    }
                ))
        
        return web.json_response(
            standard_response(success=False, error="Transaction not found"),
            status=404
        )
    
    except Exception as e:
        return web.json_response(
            standard_response(success=False, error=str(e)),
            status=500
        )


@routes.get("/api/v1/tx/history/{address}")
async def get_transaction_history(request):
    """
    Get transaction history for an address
    
    Path:
        - address: PHN address
    
    Query params:
        - limit: Maximum transactions to return (default 50, max 500)
        - offset: Pagination offset (default 0)
        - type: Filter by type (all, sent, received)
    
    Returns:
        - transactions: List of transactions
        - total: Total transaction count
    """
    try:
        address = request.match_info['address']
        limit = min(int(request.query.get('limit', 50)), 500)
        offset = int(request.query.get('offset', 0))
        tx_type = request.query.get('type', 'all')
        
        # Collect all transactions
        transactions = []
        
        for block in blockchain:
            for tx in block.get("transactions", []):
                sender = tx.get("sender")
                recipient = tx.get("recipient")
                
                include = False
                direction = None
                
                if tx_type == 'all':
                    if sender == address or recipient == address:
                        include = True
                        direction = "sent" if sender == address else "received"
                elif tx_type == 'sent' and sender == address:
                    include = True
                    direction = "sent"
                elif tx_type == 'received' and recipient == address:
                    include = True
                    direction = "received"
                
                if include:
                    transactions.append({
                        "txid": tx.get("txid"),
                        "block": block.get("index"),
                        "timestamp": block.get("timestamp"),
                        "direction": direction,
                        "sender": sender,
                        "recipient": recipient,
                        "amount": tx.get("amount"),
                        "fee": tx.get("fee"),
                        "confirmations": len(blockchain) - block.get("index")
                    })
        
        # Add pending transactions
        for tx in pending_txs:
            sender = tx.get("sender")
            recipient = tx.get("recipient")
            
            if sender == address or recipient == address:
                transactions.append({
                    "txid": tx.get("txid"),
                    "block": None,
                    "timestamp": tx.get("timestamp"),
                    "direction": "sent" if sender == address else "received",
                    "sender": sender,
                    "recipient": recipient,
                    "amount": tx.get("amount"),
                    "fee": tx.get("fee"),
                    "status": "pending"
                })
        
        # Sort by timestamp (newest first) and paginate
        transactions.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
        total = len(transactions)
        transactions = transactions[offset:offset + limit]
        
        return web.json_response(standard_response(
            success=True,
            data={
                "address": address,
                "transactions": transactions,
                "total": total,
                "limit": limit,
                "offset": offset
            }
        ))
    
    except Exception as e:
        return web.json_response(
            standard_response(success=False, error=str(e)),
            status=500
        )


@routes.get("/api/v1/tx/pending")
async def get_pending_transactions(request):
    """
    Get pending transactions in mempool
    
    Query params:
        - limit: Maximum transactions (default 50, max 500)
        - sort: Sort by 'fee' or 'time' (default 'fee')
    
    Returns:
        - transactions: List of pending transactions
    """
    try:
        limit = min(int(request.query.get('limit', 50)), 500)
        sort_by = request.query.get('sort', 'fee')
        
        # Sort transactions
        sorted_txs = pending_txs.copy()
        
        if sort_by == 'fee':
            sorted_txs.sort(key=lambda x: float(x.get("fee", 0)), reverse=True)
        else:  # sort by time
            sorted_txs.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
        
        # Limit results
        sorted_txs = sorted_txs[:limit]
        
        # Calculate stats
        total_fees = sum(float(tx.get("fee", 0)) for tx in pending_txs)
        avg_fee = total_fees / len(pending_txs) if pending_txs else 0
        
        return web.json_response(standard_response(
            success=True,
            data={
                "transactions": sorted_txs,
                "count": len(sorted_txs),
                "total_pending": len(pending_txs),
                "total_fees": total_fees,
                "average_fee": avg_fee
            }
        ))
    
    except Exception as e:
        return web.json_response(
            standard_response(success=False, error=str(e)),
            status=500
        )


@routes.post("/api/v1/tx/broadcast")
async def broadcast_transaction(request):
    """
    Broadcast a signed transaction
    (Alias for /api/v1/tx/send for compatibility)
    """
    return await send_transaction(request)


# Legacy endpoints for backward compatibility
@routes.post("/send_tx")
async def legacy_send_tx(request):
    """Legacy endpoint - redirects to new API"""
    return await send_transaction(request)


@routes.post("/get_pending")
async def legacy_get_pending(request):
    """Legacy endpoint - returns pending transactions"""
    try:
        txs = pending_txs.copy()
        txs.sort(key=lambda x: float(x.get("fee", 0)), reverse=True)
        
        return web.json_response({
            "pending_transactions": txs,
            "count": len(txs)
        })
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


@routes.post("/get_balance")
async def legacy_get_balance(request):
    """Legacy endpoint - returns balance"""
    try:
        data = await request.json()
        addr = data.get("address")
        
        if not addr:
            return web.json_response({"error": "address required"}, status=400)
        
        bal = get_balance(addr)
        return web.json_response({"address": addr, "balance": bal})
    
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


@routes.post("/get_transaction")
async def legacy_get_transaction(request):
    """Legacy endpoint - returns transaction"""
    try:
        data = await request.json()
        txid = data.get("txid")
        
        if not txid:
            return web.json_response({"error": "txid required"}, status=400)
        
        for block in blockchain:
            for tx in block.get("transactions", []):
                if tx.get("txid") == txid:
                    return web.json_response({
                        "tx": tx,
                        "block_index": block.get("index")
                    })
        
        for tx in pending_txs:
            if tx.get("txid") == txid:
                return web.json_response({
                    "tx": tx,
                    "block_index": None
                })
        
        return web.json_response({"error": "not found"}, status=404)
    
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)
