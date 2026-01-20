import asyncio
import os
import time
import threading
from pathlib import Path
from aiohttp import web
import aiohttp
import requests
from dotenv import load_dotenv
from collections import defaultdict
from functools import wraps

# Load environment variables early
load_dotenv()

# Import blockchain core logic and config
from app.core.blockchain.chain import (
    blockchain, pending_txs, peers,
    load_blockchain, save_blockchain, create_genesis_block,
    validate_transaction, validate_block, get_balance,
    get_current_block_reward, calculate_total_mined, verify_blockchain, load_owner_address,
    init_database, save_pending_transactions, load_pending_transactions, save_peers, load_peers,
    public_key_to_address
)
from app.core.config import settings
from app.core.consensus.difficulty import DifficultyAdjuster
from app.core.transactions.mempool import AdvancedMempool
from app.core.security.protection import ChainProtection
from app.core.network.sync import RobustNodeSync

# Constants and paths
ROOT = Path(__file__).resolve().parent

# SECURITY FIX: Add mutex for race condition protection
blockchain_lock = threading.Lock()
mempool_lock = threading.Lock()

# Initialize advanced systems
difficulty_adjuster = DifficultyAdjuster(
    target_block_time=60,  # 60 seconds per block
    adjustment_interval=10  # Adjust every 10 blocks
)

# Initialize advanced mempool (replaces simple pending_txs list)
advanced_mempool = AdvancedMempool(
    max_size=10000,  # Max 10,000 transactions
    max_tx_age=3600  # Transactions expire after 1 hour
)

# Initialize chain protection (51% attack mitigation)
chain_protection = ChainProtection(
    checkpoint_interval=100,  # Checkpoint every 100 blocks
    max_reorg_depth=10        # Max 10 blocks reorganization allowed
)

# Initialize robust node synchronization with failure handling
node_sync = RobustNodeSync(
    blockchain=blockchain,
    peers=peers,
    verify_blockchain=verify_blockchain,
    save_blockchain=save_blockchain
)
print("[init] Robust node synchronization initialized")

# Rate Limiting System - Protects against DDoS attacks
class RateLimiter:
    """
    Simple but effective rate limiter for API endpoints
    Tracks requests per IP address with configurable limits
    """
    def __init__(self):
        self.requests = defaultdict(list)  # ip -> [timestamp, timestamp, ...]
        self.limits = {
            'default': (100, 60),      # 100 requests per 60 seconds
            'send_tx': (10, 60),       # 10 transactions per 60 seconds
            'submit_block': (20, 60),  # 20 block submissions per 60 seconds
            'get_balance': (50, 60),   # 50 balance checks per 60 seconds
        }
    
    def is_allowed(self, ip: str, endpoint: str = 'default') -> tuple[bool, str]:
        """Check if request from IP is allowed"""
        current_time = time.time()
        
        # Get limit for endpoint
        max_requests, time_window = self.limits.get(endpoint, self.limits['default'])
        
        # Clean old requests
        self.requests[ip] = [t for t in self.requests[ip] if current_time - t < time_window]
        
        # Check limit
        if len(self.requests[ip]) >= max_requests:
            return False, f"Rate limit exceeded: max {max_requests} requests per {time_window}s"
        
        # Allow request
        self.requests[ip].append(current_time)
        return True, "ok"
    
    def get_stats(self, ip: str) -> dict:
        """Get rate limit stats for IP"""
        current_time = time.time()
        recent_requests = [t for t in self.requests[ip] if current_time - t < 60]
        return {
            "ip": ip,
            "requests_last_minute": len(recent_requests),
            "total_tracked_requests": len(self.requests[ip])
        }

rate_limiter = RateLimiter()

def rate_limit(endpoint: str = 'default'):
    """Decorator for rate limiting endpoints"""
    def decorator(handler):
        @wraps(handler)
        async def wrapper(request):
            # Get client IP
            ip = request.remote
            
            # Check rate limit
            allowed, msg = rate_limiter.is_allowed(ip, endpoint)
            if not allowed:
                print(f"[RATE LIMIT] Blocked {ip} on {endpoint}: {msg}")
                return web.json_response({"error": msg}, status=429)
            
            # Allow request
            return await handler(request)
        return wrapper
    return decorator

# Token config from environment
COIN_LOGO = r"""
   ____  _  _ _   _  _   _ 
  |  _ \| || | \ | |/ \ | |
  | |_) | || |  \| / _ \| |
  |  __/|__   _|\  / ___ \ |
  |_|      |_|   \/ /   \_|
      PHN NETWORK NODE
"""

def startup_load():
    """Load blockchain and initialize system"""
    init_database()
    
    # Load blockchain from LMDB
    blockchain_loaded = load_blockchain()
    if not blockchain_loaded:
        print("[startup] No blockchain found or invalid, creating genesis block")
        blockchain.clear()
        blockchain.append(create_genesis_block())
        save_blockchain()
    
    load_pending_transactions()
    load_peers()
    
    # Add configured peers
    for p in settings.PEERS:
        if isinstance(p, str) and p.startswith("http"):
            peers.add(p)
    
    save_peers()

# OLD SYNC FUNCTION - REPLACED BY RobustNodeSync
# Kept for reference only - no longer used
# async def sync_with_peer(peer_url: str) -> bool:
#     """Sync blockchain with a peer node"""
#     try:
#         url = peer_url.rstrip("/") + "/get_blockchain"
#         res = requests.post(url, timeout=5)
#         if res.status_code != 200:
#             return False
#         data = res.json()
#         their_chain = data.get("blockchain")
#         if not their_chain:
#             return False
#         if len(their_chain) > len(blockchain):
#             ok, _ = verify_blockchain(their_chain)
#             if ok:
#                 print(f"[sync] Adopting longer chain from {peer_url} length {len(their_chain)}")
#                 blockchain.clear()
#                 blockchain.extend(their_chain)
#                 save_blockchain()
#                 return True
#     except Exception as e:
#         print(f"[sync] Error syncing with {peer_url}: {e}")
#         return False
#     return False

async def broadcast_block_to_peers(block: dict):
    """
    Gossip Protocol: Broadcast newly mined block to all peers using RobustNodeSync.
    This ensures fast propagation across the network with automatic failure handling.
    """
    return await node_sync.broadcast_block(block)

async def periodic_peer_sync(interval_sec: int = 30):
    """
    Periodic blockchain synchronization using RobustNodeSync with health monitoring.
    This is now just a wrapper that starts the robust periodic sync.
    """
    await node_sync.periodic_sync(interval_sec)

# HTTP routes
routes = web.RouteTableDef()

@routes.get("/")
async def index(request):
    owner_bal = get_balance(load_owner_address())
    info = (
        f"Node version: {settings.NODE_VERSION}\n"
        f"Blocks: {len(blockchain)}\n"
        f"Pending TX: {len(pending_txs)}\n"
        f"Owner: {load_owner_address()}\n"
        f"Owner Balance: {owner_bal:.6f} {settings.TOKEN_SYMBOL}\n"
        f"Total Supply: {settings.TOTAL_SUPPLY:,} {settings.TOKEN_SYMBOL}\n"
        f"Storage: LMDB (Lightning Memory-Mapped Database)\n"
    )
    logo_hint = "/phn.png or /logo"
    return web.Response(text=COIN_LOGO + "\n" + info + "\nLogo: " + logo_hint)

@routes.get("/phn.png")
@routes.get("/logo")
async def phn_logo(request):
    if settings.LOGO_PATH.exists():
        return web.FileResponse(path=settings.LOGO_PATH)
    if settings.LOGO_URL:
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=3)) as session:
                async with session.get(settings.LOGO_URL) as resp:
                    if resp.status == 200:
                        data = await resp.read()
                        return web.Response(body=data, content_type="image/png")
                    return web.Response(text=f"Failed to fetch remote logo: {resp.status}", status=resp.status)
        except Exception as e:
            return web.Response(text=f"Error fetching remote logo: {e}", status=500)
    return web.Response(text="No logo available", status=404)

@routes.get("/token_info")
async def token_info(request):
    total_mined = calculate_total_mined()
    supply_left = settings.TOTAL_SUPPLY - total_mined
    company_holdings = get_balance(load_owner_address())
    return web.json_response({
        "name": settings.TOKEN_NAME,
        "logo_url": settings.LOGO_URL or request.url.with_path("/phn.png").human_repr(),
        "total_supply": settings.TOTAL_SUPPLY,
        "company_holdings": company_holdings,
        "circulating_supply": total_mined,
        "supply_left": supply_left,
        "storage_type": "LMDB"
    })

@routes.get("/mining_info")
async def mining_info(request):
    """Get mining information for miners with dynamic difficulty"""
    # Calculate dynamic difficulty based on recent blocks
    current_difficulty = difficulty_adjuster.calculate_difficulty(blockchain)
    
    return web.json_response({
        "difficulty": current_difficulty,
        "block_reward": get_current_block_reward(),
        "min_tx_fee": settings.MIN_TX_FEE,
        "current_block_height": len(blockchain),
        "pending_transactions": advanced_mempool.get_size(),
        "owner_address": load_owner_address(),
        "target_block_time": difficulty_adjuster.target_block_time,
        "mempool_stats": advanced_mempool.get_statistics()
    })

@routes.post("/peers")
async def list_peers(request):
    return web.json_response({"peers": list(peers)})

@routes.post("/add_peer")
async def add_peer(request):
    data = await request.json()
    p = data.get("peer")
    if not p or not p.startswith("http"):
        return web.json_response({"error": "valid peer URL required"}, status=400)
    peers.add(p)
    save_peers()  # Save peers to storage
    await node_sync.sync_with_peer(p)  # Use robust sync
    return web.json_response({"status": "ok", "peers": list(peers)})

@routes.post("/send_tx")
@rate_limit('send_tx')  # Rate limit: 10 transactions per 60 seconds
async def http_send_tx(request):
    data = await request.json()
    tx = data.get("tx")
    if not tx:
        return web.json_response({"error": "tx missing"}, status=400)
    
    # SECURITY FIX: Use lock to prevent race condition (Bug #3)
    with mempool_lock:
        # Get sender - could be public key or PHN address
        sender = tx.get("sender")
        if not sender:
            return web.json_response({"error": "sender missing"}, status=400)
        
        # For balance checking, if sender is a public key, convert to PHN address
        if len(sender) == 128:  # Public key format
            balance_address = public_key_to_address(sender)
            print(f"[DEBUG] Converted public key to PHN address: {balance_address}")
        else:
            balance_address = sender
        
        # Check balance using the appropriate address format
        sender_balance = get_balance(balance_address)
        total_needed = float(tx.get("amount", 0)) + float(tx.get("fee", 0))
        
        print(f"[DEBUG] Sender: {sender[:32]}...")
        print(f"[DEBUG] Balance address: {balance_address}")
        print(f"[DEBUG] Sender balance: {sender_balance}")
        print(f"[DEBUG] Total needed: {total_needed}")
        
        if sender_balance < total_needed:
            return web.json_response({"error": f"Insufficient balance. Need {total_needed}, have {sender_balance}"}, status=400)
        
        ok, msg = validate_transaction(tx)
        if not ok:
            return web.json_response({"error": msg}, status=400)
        
        # Use advanced mempool instead of pending_txs list
        success, mempool_msg = advanced_mempool.add_transaction(tx)
        if not success:
            return web.json_response({"error": mempool_msg}, status=400)
        
        # Also add to legacy pending_txs for backward compatibility
        if not any(t["txid"] == tx["txid"] for t in pending_txs):
            pending_txs.append(tx)
            save_pending_transactions()
        
        print(f"[DEBUG] Transaction added to mempool: {tx['txid']}")
        return web.json_response({"status": "success", "txid": tx["txid"], "mempool_position": advanced_mempool.get_size()})

@routes.post("/get_pending")
async def http_get_pending(request):
    """Get pending transactions sorted by fee (highest first)"""
    # Get transactions from advanced mempool (sorted by fee)
    mempool_txs = advanced_mempool.get_transactions_for_mining(max_count=1000)
    
    return web.json_response({
        "pending_transactions": mempool_txs, 
        "count": len(mempool_txs),
        "mempool_stats": advanced_mempool.get_statistics()
    })

@routes.post("/get_balance")
@rate_limit('get_balance')  # Rate limit: 50 requests per 60 seconds
async def http_get_balance(request):
    data = await request.json()
    addr = data.get("address")
    if not addr:
        return web.json_response({"error": "address required"}, status=400)
    bal = get_balance(addr)
    return web.json_response({"address": addr, "balance": bal})

@routes.post("/get_blockchain")
async def http_get_blockchain(request):
    return web.json_response({"blockchain": blockchain, "length": len(blockchain)})

@routes.post("/get_transaction")
async def http_get_transaction(request):
    data = await request.json()
    txid = data.get("txid")
    if not txid:
        return web.json_response({"error": "txid required"}, status=400)
    for block in blockchain:
        for tx in block.get("transactions", []):
            if tx.get("txid") == txid:
                return web.json_response({"tx": tx, "block_index": block.get("index")})
    for tx in pending_txs:
        if tx.get("txid") == txid:
            return web.json_response({"tx": tx, "block_index": None})
    return web.json_response({"error": "not found"}, status=404)

@routes.post("/submit_block")
@rate_limit('submit_block')  # Rate limit: 20 blocks per 60 seconds
async def http_submit_block(request):
    """
    Submit a newly mined block. Uses gossip protocol to broadcast to all peers.
    This ensures fast block propagation across the network.
    """
    data = await request.json()
    block = data.get("block")
    if not block:
        return web.json_response({"error": "block missing"}, status=400)
    
    ok, msg = validate_block(block)
    if not ok:
        return web.json_response({"status": "error", "message": msg}, status=400)
    
    blockchain.append(block)
    save_blockchain()
    
    # SECURITY: Auto-checkpoint new block (51% attack protection)
    chain_protection.auto_checkpoint_new_block(blockchain)
    
    # Validate chain against checkpoints
    valid, checkpoint_msg = chain_protection.validate_chain_against_checkpoints(blockchain)
    if not valid:
        # SECURITY ALERT: Checkpoint violation detected!
        print(f"[SECURITY] {checkpoint_msg}")
        return web.json_response({
            "status": "error", 
            "message": "Checkpoint violation - possible attack detected"
        }, status=400)
    
    # Remove mined transactions from both pending and mempool
    mined_txids = {tx["txid"] for tx in block.get("transactions", []) if tx.get("sender") not in ["coinbase", "miners_pool"]}
    
    # Remove from legacy pending_txs
    pending_txs[:] = [t for t in pending_txs if t["txid"] not in mined_txids]
    save_pending_transactions()
    
    # Remove from advanced mempool
    advanced_mempool.remove_transactions(list(mined_txids))
    
    # Gossip protocol: Broadcast block to all peers for fast propagation
    asyncio.create_task(broadcast_block_to_peers(block))
    
    # Log difficulty adjustment info
    current_diff = difficulty_adjuster.calculate_difficulty(blockchain)
    print(f"[Block #{block['index']}] Accepted - Current difficulty: {current_diff}")
    
    return web.json_response({"status": "accepted", "index": block["index"], "current_difficulty": current_diff})

# Application setup
app = web.Application()
app.add_routes(routes)

# Import and register new API endpoint routes
try:
    from app.api.v1.endpoints.balance import routes as balance_routes
    from app.api.v1.endpoints.explorer import routes as explorer_routes
    from app.api.v1.endpoints.tokens import routes as tokens_routes
    from app.api.v1.endpoints.assets_api import routes as assets_routes
    app.add_routes(balance_routes)
    app.add_routes(explorer_routes)
    app.add_routes(tokens_routes)
    app.add_routes(assets_routes)
    print("[API] ✓ Loaded new API endpoints: balance, explorer, tokens, assets")
except ImportError as e:
    print(f"[API] Warning: Could not load some API endpoints: {e}")

async def on_startup(app):
    startup_load()
    # Sync with all peers using robust sync
    for p in list(peers):
        try:
            await node_sync.sync_with_peer(p)
        except Exception as e:
            print(f"[startup] Failed to sync with {p}: {e}")
    
    # Start periodic sync task
    app["peer_sync_task"] = asyncio.create_task(periodic_peer_sync(30))

async def on_cleanup(app):
    task = app.get("peer_sync_task")
    if task:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    save_blockchain()
    save_pending_transactions()
    save_peers()

app.on_startup.append(on_startup)
app.on_cleanup.append(on_cleanup)

if __name__ == "__main__":
    print(COIN_LOGO)
    web.run_app(app, host=settings.NODE_HOST, port=settings.NODE_PORT)
