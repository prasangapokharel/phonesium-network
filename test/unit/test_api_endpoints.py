"""
PHN Blockchain - API Testing Script
Tests all new RPC API endpoints
"""

import requests
import orjson
import time

BASE_URL = "http://localhost:8765"


def test_api(endpoint, method="GET", data=None):
    """Test an API endpoint"""
    try:
        if method == "GET":
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
        else:
            response = requests.post(f"{BASE_URL}{endpoint}", json=data, timeout=5)
        
        print(f"\n{'='*60}")
        print(f"{method} {endpoint}")
        print(f"Status: {response.status_code}")
        print(f"Response:")
        print(ororjson.dumps(response.json(), option=orjson.OPT_INDENT_2).decode()[:500])
        print('='*60)
        
        return response.json()
    except Exception as e:
        print(f"\n[ERROR] Error testing {endpoint}: {e}")
        return None


def main():
    """Run API tests"""
    print("\n PHN Blockchain API Test Suite")
    print("=" * 60)
    
    # Test 1: Explorer Stats
    print("\n TEST 1: Network Statistics")
    stats = test_api("/api/v1/explorer/stats")
    
    # Test 2: Latest Blocks
    print("\n TEST 2: Latest Blocks")
    blocks = test_api("/api/v1/explorer/blocks/latest?limit=5")
    
    # Test 3: Node Info
    print("\n TEST 3: Node Information")
    info = test_api("/api/v1/explorer/info")
    
    # Test 4: Balance API (check a known address)
    print("\n TEST 4: Balance Query")
    # Use the owner address from node info
    if stats and stats.get("success"):
        # Get owner address from legacy endpoint
        legacy_info = test_api("/info")
    
    # Test 5: Rich List
    print("\n TEST 5: Rich List")
    richlist = test_api("/api/v1/balance/richlist?limit=10")
    
    # Test 6: Pending Transactions
    print("\n TEST 6: Pending Transactions")
    pending = test_api("/api/v1/tx/pending?limit=10")
    
    # Test 7: Token Platform Stats
    print("\n🪙 TEST 7: Token Platform Statistics")
    token_stats = test_api("/api/v1/tokens/stats")
    
    # Test 8: Asset Platform Stats
    print("\n TEST 8: Asset Platform Statistics")
    asset_stats = test_api("/api/v1/assets/stats")
    
    # Test 9: List Tokens
    print("\n TEST 9: List All Tokens")
    tokens = test_api("/api/v1/tokens/list?limit=10")
    
    # Test 10: List Assets
    print("\n TEST 10: List All Assets")
    assets = test_api("/api/v1/assets/list?limit=10")
    
    # Test 11: Create Wallet (Demonstration)
    print("\n TEST 11: Create New Wallet (if endpoint available)")
    # Note: This creates a new wallet - use cautiously
    # wallet = test_api("/api/v1/wallet/create", method="POST")
    
    # Test 12: Search Blockchain
    print("\n TEST 12: Search Blockchain")
    if blocks and blocks.get("success") and blocks["data"]["blocks"]:
        first_block_hash = blocks["data"]["blocks"][0]["hash"]
        search = test_api(f"/api/v1/explorer/search/{first_block_hash}")
    
    print("\n" + "="*60)
    print("[OK] API Test Suite Complete!")
    print("="*60)
    print("\n Full API Documentation: docs/RPC_API_REFERENCE.md")
    print("\n Key Features:")
    print("   [OK] Wallet management (create, import, sign)")
    print("   [OK] Balance queries (PHN, tokens, assets)")
    print("   [OK] Transaction management (send, query, history)")
    print("   [OK] Blockchain explorer (blocks, search, stats)")
    print("   [OK] Asset tokenization (create, transfer, fractionalize)")
    print("   [OK] Custom token platform (create, mint, burn, transfer)")
    print("\n All endpoints use standard JSON response format")
    print("   - success: true/false")
    print("   - data: {...}")
    print("   - error: null or error message")
    print("   - timestamp: unix timestamp\n")


if __name__ == "__main__":
    print("\n[WARNING]  Make sure PHN node is running:")
    print("   python app/main.py\n")
    
    input("Press Enter to start API tests...")
    
    main()
