"""
PHN Blockchain - Token Platform API Endpoints
Create custom tokens on PHN blockchain (like ERC-20)
"""

from aiohttp import web
import time
import hashlib
import secrets
from typing import Dict
from app.core.blockchain.chain import get_balance

routes = web.RouteTableDef()

# In-memory token storage (in production, use LMDB)
tokens_db = {}
token_balances = {}  # {token_id: {address: balance}}


def standard_response(success: bool, data=None, error=None):
    """Standard API response format"""
    return {
        "success": success,
        "data": data,
        "error": error,
        "timestamp": int(time.time())
    }


def generate_token_id() -> str:
    """Generate unique token ID"""
    random_bytes = secrets.token_bytes(16)
    timestamp = str(time.time()).encode()
    return hashlib.sha256(random_bytes + timestamp).hexdigest()[:16].upper()


@routes.post("/api/v1/token/create")
async def create_token(request):
    """
    Create a custom token on PHN blockchain
    
    Body:
        - name: Token name (e.g., "MyToken")
        - symbol: Token symbol (e.g., "MTK")
        - total_supply: Total supply (e.g., 1000000)
        - decimals: Decimal places (default 8)
        - owner_address: Token creator address
        - description: Token description
        - metadata: Additional metadata
    
    Returns:
        - token_id: Unique token identifier
        - token: Token details
    """
    try:
        data = await request.json()
        
        # Validate required fields
        required = ["name", "symbol", "total_supply", "owner_address"]
        for field in required:
            if field not in data:
                return web.json_response(
                    standard_response(success=False, error=f"Missing field: {field}"),
                    status=400
                )
        
        # Generate token ID
        token_id = generate_token_id()
        
        # Create token
        token = {
            "token_id": token_id,
            "name": data["name"],
            "symbol": data["symbol"].upper(),
            "total_supply": float(data["total_supply"]),
            "decimals": int(data.get("decimals", 8)),
            "owner_address": data["owner_address"],
            "description": data.get("description", ""),
            "metadata": data.get("metadata", {}),
            "created_at": int(time.time()),
            "mintable": data.get("mintable", False),
            "burnable": data.get("burnable", True),
            "standard": "PHN-20"  # PHN equivalent of ERC-20
        }
        
        # Store token
        tokens_db[token_id] = token
        
        # Initialize balances (owner gets all supply)
        token_balances[token_id] = {
            data["owner_address"]: float(data["total_supply"])
        }
        
        return web.json_response(standard_response(
            success=True,
            data={
                "token_id": token_id,
                "token": token,
                "message": f"Token {token['symbol']} created successfully"
            }
        ))
    
    except Exception as e:
        return web.json_response(
            standard_response(success=False, error=str(e)),
            status=500
        )


@routes.post("/api/v1/token/mint")
async def mint_tokens(request):
    """
    Mint additional tokens (only if token is mintable)
    
    Body:
        - token_id: Token identifier
        - to_address: Recipient address
        - amount: Amount to mint
        - signature: Owner signature
    
    Returns:
        - new_supply: Updated total supply
        - balance: Recipient's new balance
    """
    try:
        data = await request.json()
        
        # Validate required fields
        required = ["token_id", "to_address", "amount", "signature"]
        for field in required:
            if field not in data:
                return web.json_response(
                    standard_response(success=False, error=f"Missing field: {field}"),
                    status=400
                )
        
        token_id = data["token_id"]
        
        # Check if token exists
        if token_id not in tokens_db:
            return web.json_response(
                standard_response(success=False, error="Token not found"),
                status=404
            )
        
        token = tokens_db[token_id]
        
        # Check if mintable
        if not token.get("mintable", False):
            return web.json_response(
                standard_response(success=False, error="Token is not mintable"),
                status=400
            )
        
        # Mint tokens
        amount = float(data["amount"])
        to_address = data["to_address"]
        
        # Update balances
        if token_id not in token_balances:
            token_balances[token_id] = {}
        
        token_balances[token_id][to_address] = token_balances[token_id].get(to_address, 0) + amount
        token["total_supply"] += amount
        
        return web.json_response(standard_response(
            success=True,
            data={
                "token_id": token_id,
                "minted": amount,
                "to": to_address,
                "new_balance": token_balances[token_id][to_address],
                "new_supply": token["total_supply"]
            }
        ))
    
    except Exception as e:
        return web.json_response(
            standard_response(success=False, error=str(e)),
            status=500
        )


@routes.post("/api/v1/token/burn")
async def burn_tokens(request):
    """
    Burn (destroy) tokens
    
    Body:
        - token_id: Token identifier
        - from_address: Burner address
        - amount: Amount to burn
        - signature: Signature
    
    Returns:
        - burned: Amount burned
        - new_supply: Updated total supply
    """
    try:
        data = await request.json()
        
        # Validate required fields
        required = ["token_id", "from_address", "amount", "signature"]
        for field in required:
            if field not in data:
                return web.json_response(
                    standard_response(success=False, error=f"Missing field: {field}"),
                    status=400
                )
        
        token_id = data["token_id"]
        
        # Check if token exists
        if token_id not in tokens_db:
            return web.json_response(
                standard_response(success=False, error="Token not found"),
                status=404
            )
        
        token = tokens_db[token_id]
        
        # Check if burnable
        if not token.get("burnable", False):
            return web.json_response(
                standard_response(success=False, error="Token is not burnable"),
                status=400
            )
        
        # Burn tokens
        amount = float(data["amount"])
        from_address = data["from_address"]
        
        # Check balance
        current_balance = token_balances.get(token_id, {}).get(from_address, 0)
        if current_balance < amount:
            return web.json_response(
                standard_response(success=False, error=f"Insufficient balance. Have {current_balance}, need {amount}"),
                status=400
            )
        
        # Update balances
        token_balances[token_id][from_address] -= amount
        token["total_supply"] -= amount
        
        return web.json_response(standard_response(
            success=True,
            data={
                "token_id": token_id,
                "burned": amount,
                "from": from_address,
                "new_balance": token_balances[token_id][from_address],
                "new_supply": token["total_supply"]
            }
        ))
    
    except Exception as e:
        return web.json_response(
            standard_response(success=False, error=str(e)),
            status=500
        )


@routes.post("/api/v1/token/transfer")
async def transfer_tokens(request):
    """
    Transfer tokens between addresses
    
    Body:
        - token_id: Token identifier
        - from_address: Sender address
        - to_address: Recipient address
        - amount: Amount to transfer
        - signature: Sender signature
    
    Returns:
        - transfer: Transfer details
    """
    try:
        data = await request.json()
        
        # Validate required fields
        required = ["token_id", "from_address", "to_address", "amount", "signature"]
        for field in required:
            if field not in data:
                return web.json_response(
                    standard_response(success=False, error=f"Missing field: {field}"),
                    status=400
                )
        
        token_id = data["token_id"]
        
        # Check if token exists
        if token_id not in tokens_db:
            return web.json_response(
                standard_response(success=False, error="Token not found"),
                status=404
            )
        
        # Transfer tokens
        amount = float(data["amount"])
        from_address = data["from_address"]
        to_address = data["to_address"]
        
        # Check balance
        current_balance = token_balances.get(token_id, {}).get(from_address, 0)
        if current_balance < amount:
            return web.json_response(
                standard_response(success=False, error=f"Insufficient balance. Have {current_balance}, need {amount}"),
                status=400
            )
        
        # Update balances
        if token_id not in token_balances:
            token_balances[token_id] = {}
        
        token_balances[token_id][from_address] -= amount
        token_balances[token_id][to_address] = token_balances[token_id].get(to_address, 0) + amount
        
        return web.json_response(standard_response(
            success=True,
            data={
                "token_id": token_id,
                "from": from_address,
                "to": to_address,
                "amount": amount,
                "from_balance": token_balances[token_id][from_address],
                "to_balance": token_balances[token_id][to_address]
            }
        ))
    
    except Exception as e:
        return web.json_response(
            standard_response(success=False, error=str(e)),
            status=500
        )


@routes.get("/api/v1/token/{token_id}")
async def get_token_info(request):
    """
    Get token information
    
    Path:
        - token_id: Token identifier
    
    Returns:
        - token: Token details
    """
    try:
        token_id = request.match_info['token_id']
        
        if token_id not in tokens_db:
            return web.json_response(
                standard_response(success=False, error="Token not found"),
                status=404
            )
        
        token = tokens_db[token_id]
        
        # Add holder count
        holders = len([addr for addr, bal in token_balances.get(token_id, {}).items() if bal > 0])
        
        return web.json_response(standard_response(
            success=True,
            data={
                **token,
                "holders": holders
            }
        ))
    
    except Exception as e:
        return web.json_response(
            standard_response(success=False, error=str(e)),
            status=500
        )


@routes.get("/api/v1/token/balance/{token_id}/{address}")
async def get_token_balance(request):
    """
    Get token balance for an address
    
    Path:
        - token_id: Token identifier
        - address: PHN address
    
    Returns:
        - balance: Token balance
    """
    try:
        token_id = request.match_info['token_id']
        address = request.match_info['address']
        
        if token_id not in tokens_db:
            return web.json_response(
                standard_response(success=False, error="Token not found"),
                status=404
            )
        
        balance = token_balances.get(token_id, {}).get(address, 0)
        token = tokens_db[token_id]
        
        return web.json_response(standard_response(
            success=True,
            data={
                "token_id": token_id,
                "token_symbol": token["symbol"],
                "address": address,
                "balance": balance
            }
        ))
    
    except Exception as e:
        return web.json_response(
            standard_response(success=False, error=str(e)),
            status=500
        )


@routes.get("/api/v1/token/supply/{token_id}")
async def get_token_supply(request):
    """
    Get token supply information
    
    Path:
        - token_id: Token identifier
    
    Returns:
        - supply: Supply details
    """
    try:
        token_id = request.match_info['token_id']
        
        if token_id not in tokens_db:
            return web.json_response(
                standard_response(success=False, error="Token not found"),
                status=404
            )
        
        token = tokens_db[token_id]
        
        # Calculate circulating supply (non-zero balances)
        circulating = sum(bal for bal in token_balances.get(token_id, {}).values() if bal > 0)
        
        return web.json_response(standard_response(
            success=True,
            data={
                "token_id": token_id,
                "token_symbol": token["symbol"],
                "total_supply": token["total_supply"],
                "circulating_supply": circulating,
                "holders": len([addr for addr, bal in token_balances.get(token_id, {}).items() if bal > 0])
            }
        ))
    
    except Exception as e:
        return web.json_response(
            standard_response(success=False, error=str(e)),
            status=500
        )


@routes.get("/api/v1/tokens/list")
async def list_tokens(request):
    """
    List all tokens
    
    Query params:
        - limit: Max results (default 50)
        - offset: Pagination offset (default 0)
    
    Returns:
        - tokens: List of tokens
    """
    try:
        limit = min(int(request.query.get('limit', 50)), 500)
        offset = int(request.query.get('offset', 0))
        
        # Get all tokens
        all_tokens = list(tokens_db.values())
        
        # Sort by creation time
        all_tokens.sort(key=lambda x: x.get("created_at", 0), reverse=True)
        
        # Add holder counts
        for token in all_tokens:
            token_id = token["token_id"]
            token["holders"] = len([addr for addr, bal in token_balances.get(token_id, {}).items() if bal > 0])
        
        # Paginate
        total = len(all_tokens)
        paginated_tokens = all_tokens[offset:offset + limit]
        
        return web.json_response(standard_response(
            success=True,
            data={
                "tokens": paginated_tokens,
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


@routes.get("/api/v1/tokens/holder/{address}")
async def get_tokens_by_holder(request):
    """
    Get all tokens held by an address
    
    Path:
        - address: PHN address
    
    Returns:
        - holdings: List of token holdings
    """
    try:
        address = request.match_info['address']
        
        holdings = []
        
        for token_id, balances in token_balances.items():
            balance = balances.get(address, 0)
            if balance > 0:
                token = tokens_db.get(token_id)
                if token:
                    holdings.append({
                        "token_id": token_id,
                        "token_name": token["name"],
                        "token_symbol": token["symbol"],
                        "balance": balance,
                        "decimals": token["decimals"]
                    })
        
        return web.json_response(standard_response(
            success=True,
            data={
                "address": address,
                "holdings": holdings,
                "token_count": len(holdings)
            }
        ))
    
    except Exception as e:
        return web.json_response(
            standard_response(success=False, error=str(e)),
            status=500
        )


@routes.get("/api/v1/tokens/stats")
async def get_token_stats(request):
    """
    Get token platform statistics
    
    Returns:
        - stats: Platform statistics
    """
    try:
        total_tokens = len(tokens_db)
        total_holders = len(set(addr for balances in token_balances.values() for addr, bal in balances.items() if bal > 0))
        
        mintable_count = sum(1 for token in tokens_db.values() if token.get("mintable", False))
        burnable_count = sum(1 for token in tokens_db.values() if token.get("burnable", False))
        
        return web.json_response(standard_response(
            success=True,
            data={
                "total_tokens": total_tokens,
                "total_unique_holders": total_holders,
                "mintable_tokens": mintable_count,
                "burnable_tokens": burnable_count,
                "platform": "PHN-20 Token Standard"
            }
        ))
    
    except Exception as e:
        return web.json_response(
            standard_response(success=False, error=str(e)),
            status=500
        )
