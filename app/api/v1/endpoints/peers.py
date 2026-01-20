# peers.py - API endpoints for Phonesium blockchain
from aiohttp import web
from app.core.blockchain.chain import peers, sync_with_peer
from app.settings import settings

routes = web.RouteTableDef()

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
    await sync_with_peer(p)
    return web.json_response({"status": "ok", "peers": list(peers)})