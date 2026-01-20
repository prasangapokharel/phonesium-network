# addresses.py - API endpoints for Phonesium blockchain
from aiohttp import web
from app.api.v1.endpoints.blockchain import register_address, resolve_display

routes = web.RouteTableDef()

@routes.post("/register_address")
async def http_register_address(request):
    data = await request.json()
    display = data.get("display_address")
    canonical = data.get("canonical_address")
    if not display or not canonical:
        return web.json_response({"error": "missing"}, status=400)
    register_address(display, canonical)
    return web.json_response({"status": "registered"})

@routes.post("/resolve_address")
async def http_resolve_address(request):
    data = await request.json()
    display = data.get("display_address")
    if not display:
        return web.json_response({"error": "missing"}, status=400)
    canonical = resolve_display(display)
    if not canonical:
        return web.json_response({"error": "not found"}, status=404)
    return web.json_response({"canonical_address": canonical})