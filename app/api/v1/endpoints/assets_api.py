"""
PHN Blockchain - Assets API Endpoints
Create, transfer, and query tokenized assets
"""

from aiohttp import web
import time
from app.core.assets.tokenization import Asset, AssetType, AssetStandard
from app.core.blockchain.chain import blockchain, get_balance

routes = web.RouteTableDef()

# In-memory asset storage (in production, use LMDB)
assets_db = {}


def standard_response(success: bool, data=None, error=None):
    """Standard API response format"""
    return {
        "success": success,
        "data": data,
        "error": error,
        "timestamp": int(time.time())
    }


@routes.post("/api/v1/asset/create")
async def create_asset(request):
    """
    Create a new tokenized asset
    
    Body:
        - asset_type: GOLD, LAND, REAL_ESTATE, COMMODITY, SECURITY, CUSTOM
        - name: Asset name
        - description: Asset description
        - total_supply: Total units (1 for NFT)
        - owner_address: Owner PHN address
        - metadata: Additional metadata (optional)
        - fractional: Can be fractionalized (default false)
        - standard: PHN721 or PHN1155 (default PHN721)
    
    Returns:
        - asset_id: Unique asset identifier
        - asset: Complete asset data
    """
    try:
        data = await request.json()
        
        # Validate required fields
        required = ["asset_type", "name", "description", "total_supply", "owner_address"]
        for field in required:
            if field not in data:
                return web.json_response(
                    standard_response(success=False, error=f"Missing field: {field}"),
                    status=400
                )
        
        # Parse asset type
        try:
            asset_type = AssetType[data["asset_type"].upper()]
        except KeyError:
            return web.json_response(
                standard_response(success=False, error=f"Invalid asset_type. Must be one of: {[t.value for t in AssetType]}"),
                status=400
            )
        
        # Parse standard
        standard_str = data.get("standard", "PHN721").upper().replace("-", "")
        try:
            standard = AssetStandard[standard_str]
        except KeyError:
            return web.json_response(
                standard_response(success=False, error="Invalid standard. Must be PHN721 or PHN1155"),
                status=400
            )
        
        # Create asset
        asset = Asset(
            asset_type=asset_type,
            name=data["name"],
            description=data["description"],
            total_supply=float(data["total_supply"]),
            owner_address=data["owner_address"],
            metadata=data.get("metadata", {}),
            fractional=data.get("fractional", False),
            standard=standard
        )
        
        # Store asset
        assets_db[asset.asset_id] = asset
        
        return web.json_response(standard_response(
            success=True,
            data={
                "asset_id": asset.asset_id,
                "asset": asset.to_dict()
            }
        ))
    
    except Exception as e:
        return web.json_response(
            standard_response(success=False, error=str(e)),
            status=500
        )


@routes.post("/api/v1/asset/transfer")
async def transfer_asset(request):
    """
    Transfer asset ownership
    
    Body:
        - asset_id: Asset identifier
        - from_address: Current owner address
        - to_address: New owner address
        - amount: Amount to transfer (for fractional assets)
        - signature: ECDSA signature (owner proof)
    
    Returns:
        - transfer_id: Transfer identifier
        - status: Transfer status
    """
    try:
        data = await request.json()
        
        # Validate required fields
        required = ["asset_id", "from_address", "to_address", "signature"]
        for field in required:
            if field not in data:
                return web.json_response(
                    standard_response(success=False, error=f"Missing field: {field}"),
                    status=400
                )
        
        asset_id = data["asset_id"]
        
        # Check if asset exists
        if asset_id not in assets_db:
            return web.json_response(
                standard_response(success=False, error="Asset not found"),
                status=404
            )
        
        asset = assets_db[asset_id]
        
        # Transfer asset
        amount = float(data.get("amount", 1.0))
        
        success, msg = asset.transfer(
            from_address=data["from_address"],
            to_address=data["to_address"],
            amount=amount
        )
        
        if not success:
            return web.json_response(
                standard_response(success=False, error=msg),
                status=400
            )
        
        return web.json_response(standard_response(
            success=True,
            data={
                "asset_id": asset_id,
                "from": data["from_address"],
                "to": data["to_address"],
                "amount": amount,
                "status": "transferred"
            }
        ))
    
    except Exception as e:
        return web.json_response(
            standard_response(success=False, error=str(e)),
            status=500
        )


@routes.post("/api/v1/asset/fractionalize")
async def fractionalize_asset(request):
    """
    Fractionalize an asset into shares
    
    Body:
        - asset_id: Asset identifier
        - owner_address: Owner address
        - shares: Number of shares to create
        - signature: ECDSA signature
    
    Returns:
        - asset_id: Asset identifier
        - shares: Number of shares created
    """
    try:
        data = await request.json()
        
        # Validate required fields
        required = ["asset_id", "owner_address", "shares", "signature"]
        for field in required:
            if field not in data:
                return web.json_response(
                    standard_response(success=False, error=f"Missing field: {field}"),
                    status=400
                )
        
        asset_id = data["asset_id"]
        
        # Check if asset exists
        if asset_id not in assets_db:
            return web.json_response(
                standard_response(success=False, error="Asset not found"),
                status=404
            )
        
        asset = assets_db[asset_id]
        
        # Fractionalize
        shares = int(data["shares"])
        
        success, msg = asset.fractionalize(
            owner_address=data["owner_address"],
            shares=shares
        )
        
        if not success:
            return web.json_response(
                standard_response(success=False, error=msg),
                status=400
            )
        
        return web.json_response(standard_response(
            success=True,
            data={
                "asset_id": asset_id,
                "shares": shares,
                "status": "fractionalized",
                "balance": asset.get_balance(data["owner_address"])
            }
        ))
    
    except Exception as e:
        return web.json_response(
            standard_response(success=False, error=str(e)),
            status=500
        )


@routes.get("/api/v1/asset/{asset_id}")
async def get_asset(request):
    """
    Get asset details
    
    Path:
        - asset_id: Asset identifier
    
    Returns:
        - asset: Complete asset data
    """
    try:
        asset_id = request.match_info['asset_id']
        
        if asset_id not in assets_db:
            return web.json_response(
                standard_response(success=False, error="Asset not found"),
                status=404
            )
        
        asset = assets_db[asset_id]
        
        return web.json_response(standard_response(
            success=True,
            data=asset.to_dict()
        ))
    
    except Exception as e:
        return web.json_response(
            standard_response(success=False, error=str(e)),
            status=500
        )


@routes.get("/api/v1/asset/history/{asset_id}")
async def get_asset_history(request):
    """
    Get asset transaction history
    
    Path:
        - asset_id: Asset identifier
    
    Returns:
        - history: List of asset transactions
    """
    try:
        asset_id = request.match_info['asset_id']
        
        if asset_id not in assets_db:
            return web.json_response(
                standard_response(success=False, error="Asset not found"),
                status=404
            )
        
        asset = assets_db[asset_id]
        
        return web.json_response(standard_response(
            success=True,
            data={
                "asset_id": asset_id,
                "history": asset.history
            }
        ))
    
    except Exception as e:
        return web.json_response(
            standard_response(success=False, error=str(e)),
            status=500
        )


@routes.get("/api/v1/assets/owner/{address}")
async def get_assets_by_owner(request):
    """
    Get all assets owned by an address
    
    Path:
        - address: PHN address
    
    Returns:
        - assets: List of assets
    """
    try:
        address = request.match_info['address']
        
        owned_assets = []
        
        for asset_id, asset in assets_db.items():
            balance = asset.get_balance(address)
            if balance > 0:
                asset_data = asset.to_dict()
                asset_data["owned_amount"] = balance
                owned_assets.append(asset_data)
        
        return web.json_response(standard_response(
            success=True,
            data={
                "address": address,
                "assets": owned_assets,
                "count": len(owned_assets)
            }
        ))
    
    except Exception as e:
        return web.json_response(
            standard_response(success=False, error=str(e)),
            status=500
        )


@routes.get("/api/v1/assets/type/{asset_type}")
async def get_assets_by_type(request):
    """
    Get all assets of a specific type
    
    Path:
        - asset_type: GOLD, LAND, etc.
    
    Query params:
        - limit: Max results (default 50)
    
    Returns:
        - assets: List of assets
    """
    try:
        asset_type_str = request.match_info['asset_type'].upper()
        limit = min(int(request.query.get('limit', 50)), 500)
        
        # Validate asset type
        try:
            asset_type = AssetType[asset_type_str]
        except KeyError:
            return web.json_response(
                standard_response(success=False, error=f"Invalid asset_type. Must be one of: {[t.value for t in AssetType]}"),
                status=400
            )
        
        # Find matching assets
        matching_assets = []
        
        for asset_id, asset in assets_db.items():
            if asset.asset_type == asset_type:
                matching_assets.append(asset.to_dict())
                if len(matching_assets) >= limit:
                    break
        
        return web.json_response(standard_response(
            success=True,
            data={
                "asset_type": asset_type.value,
                "assets": matching_assets,
                "count": len(matching_assets)
            }
        ))
    
    except Exception as e:
        return web.json_response(
            standard_response(success=False, error=str(e)),
            status=500
        )


@routes.get("/api/v1/assets/list")
async def list_all_assets(request):
    """
    List all assets
    
    Query params:
        - limit: Max results (default 50)
        - offset: Pagination offset (default 0)
    
    Returns:
        - assets: List of assets
    """
    try:
        limit = min(int(request.query.get('limit', 50)), 500)
        offset = int(request.query.get('offset', 0))
        
        # Get all assets
        all_assets = [asset.to_dict() for asset in assets_db.values()]
        
        # Sort by creation time
        all_assets.sort(key=lambda x: x.get("created_at", 0), reverse=True)
        
        # Paginate
        total = len(all_assets)
        paginated_assets = all_assets[offset:offset + limit]
        
        return web.json_response(standard_response(
            success=True,
            data={
                "assets": paginated_assets,
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


@routes.get("/api/v1/assets/stats")
async def get_assets_stats(request):
    """
    Get asset statistics
    
    Returns:
        - stats: Asset statistics
    """
    try:
        # Calculate stats
        total_assets = len(assets_db)
        
        by_type = {}
        for asset in assets_db.values():
            asset_type = asset.asset_type.value
            by_type[asset_type] = by_type.get(asset_type, 0) + 1
        
        fractional_count = sum(1 for asset in assets_db.values() if asset.fractional)
        nft_count = total_assets - fractional_count
        
        return web.json_response(standard_response(
            success=True,
            data={
                "total_assets": total_assets,
                "by_type": by_type,
                "fractional": fractional_count,
                "nft": nft_count
            }
        ))
    
    except Exception as e:
        return web.json_response(
            standard_response(success=False, error=str(e)),
            status=500
        )
