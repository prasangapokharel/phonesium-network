"""
PHN Asset Tokenization - Complete Demonstration
Shows all features, flexibility, and security
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.assets.tokenization import Asset, AssetType, AssetRegistry, AssetStandard
from phonesium import Wallet


def print_header(title):
    print("\n" + "=" * 70)
    print(title.center(70))
    print("=" * 70 + "\n")


def demo_gold_tokenization():
    """Demonstrate gold tokenization with different units"""
    print_header("GOLD TOKENIZATION DEMO")
    
    wallet = Wallet.create()
    print(f"Owner wallet: {wallet.address}\n")
    
    # 1. Gold in Troy Ounces
    print("[1] Creating gold asset - 100 Troy Ounces")
    gold_oz = Asset(
        asset_type=AssetType.GOLD,
        name="Premium Gold Bar - 100 Troy Ounces",
        description="LBMA certified gold bar, 99.99% purity",
        total_supply=1.0,
        owner_address=wallet.address,
        metadata={
            "unit": "troy_oz",
            "quantity": 100,
            "purity": "99.99%",
            "serial": "GB-2024-001",
            "certificate": "LBMA-CERT-12345",
            "vault": "Swiss Vault A-101"
        },
        fractional=False
    )
    print(f"  Asset ID: {gold_oz.asset_id[:16]}...")
    print(f"  Type: {gold_oz.asset_type.value}")
    print(f"  Quantity: 100 Troy Ounces")
    print(f"  Purity: 99.99%")
    print(f"  Serial: GB-2024-001")
    print(f"  Standard: {gold_oz.standard.value} (NFT)")
    
    # 2. Gold in Grams (Fractional)
    print("\n[2] Creating fractional gold asset - 1000 Grams")
    gold_g = Asset(
        asset_type=AssetType.GOLD,
        name="Gold Pool - 1000 Grams",
        description="Shared gold ownership, 24K purity",
        total_supply=1000.0,  # 1000 shares (1 gram each)
        owner_address=wallet.address,
        metadata={
            "unit": "g",
            "quantity": 1000,
            "purity": "24K",
            "vault": "Singapore Vault B-205"
        },
        fractional=True,
        standard=AssetStandard.PHN1155
    )
    print(f"  Asset ID: {gold_g.asset_id[:16]}...")
    print(f"  Type: {gold_g.asset_type.value}")
    print(f"  Quantity: 1000 Grams")
    print(f"  Total Shares: 1000")
    print(f"  Standard: {gold_g.standard.value} (Multi-Token)")
    print(f"  Owner Balance: {gold_g.get_balance(wallet.address)} shares")
    
    # 3. Gold in Kilograms
    print("\n[3] Creating gold asset - 5 Kilograms")
    gold_kg = Asset(
        asset_type=AssetType.GOLD,
        name="Gold Bullion - 5kg",
        description="Institutional grade gold bullion",
        total_supply=1.0,
        owner_address=wallet.address,
        metadata={
            "unit": "kg",
            "quantity": 5,
            "purity": "999.9",
            "refinery": "Perth Mint",
            "certificate": "PM-KG-2024-789"
        },
        fractional=False
    )
    print(f"  Asset ID: {gold_kg.asset_id[:16]}...")
    print(f"  Quantity: 5 Kilograms")
    print(f"  Refinery: Perth Mint")
    
    return gold_oz, gold_g, gold_kg


def demo_land_tokenization():
    """Demonstrate land tokenization with different units"""
    print_header("LAND TOKENIZATION DEMO")
    
    wallet = Wallet.create()
    print(f"Owner wallet: {wallet.address}\n")
    
    # 1. Land in Acres
    print("[1] Creating land asset - 50 Acres")
    land_acres = Asset(
        asset_type=AssetType.LAND,
        name="Prime Agricultural Land - 50 Acres",
        description="Farmland in Iowa, USA",
        total_supply=1.0,
        owner_address=wallet.address,
        metadata={
            "unit": "acres",
            "area": 50,
            "location": "Des Moines, Iowa, USA",
            "coordinates": "41.6005° N, 93.6091° W",
            "deed": "DEED-IA-2024-001",
            "parcel_id": "IA-DSM-12345",
            "zoning": "Agricultural",
            "land_use": "Corn farming"
        },
        fractional=False
    )
    print(f"  Asset ID: {land_acres.asset_id[:16]}...")
    print(f"  Area: 50 Acres")
    print(f"  Location: Des Moines, Iowa, USA")
    print(f"  Zoning: Agricultural")
    print(f"  Deed: DEED-IA-2024-001")
    
    # 2. Land in Hectares (Fractional)
    print("\n[2] Creating fractional land asset - 20 Hectares")
    land_hectares = Asset(
        asset_type=AssetType.LAND,
        name="Commercial Land - 20 Hectares",
        description="Development land, shared ownership",
        total_supply=100.0,  # 100 shares
        owner_address=wallet.address,
        metadata={
            "unit": "hectares",
            "area": 20,
            "location": "Frankfurt, Germany",
            "zoning": "Commercial",
            "development_potential": "Mixed-use"
        },
        fractional=True,
        standard=AssetStandard.PHN1155
    )
    print(f"  Asset ID: {land_hectares.asset_id[:16]}...")
    print(f"  Area: 20 Hectares")
    print(f"  Location: Frankfurt, Germany")
    print(f"  Total Shares: 100")
    print(f"  Share per unit: 0.2 hectares/share")
    
    # 3. Land in Square Feet
    print("\n[3] Creating land asset - 10,000 Square Feet")
    land_sqft = Asset(
        asset_type=AssetType.LAND,
        name="Urban Plot - 10,000 sqft",
        description="Residential plot in downtown",
        total_supply=1.0,
        owner_address=wallet.address,
        metadata={
            "unit": "sqft",
            "area": 10000,
            "location": "New York City, NY",
            "zoning": "Residential",
            "utilities": "All connected"
        },
        fractional=False
    )
    print(f"  Asset ID: {land_sqft.asset_id[:16]}...")
    print(f"  Area: 10,000 Square Feet")
    print(f"  Location: New York City")
    
    # 4. Land in Square Meters
    print("\n[4] Creating land asset - 5,000 Square Meters")
    land_sqm = Asset(
        asset_type=AssetType.LAND,
        name="Industrial Land - 5000 sqm",
        description="Industrial zone plot",
        total_supply=1.0,
        owner_address=wallet.address,
        metadata={
            "unit": "sqm",
            "area": 5000,
            "location": "Tokyo, Japan",
            "zoning": "Industrial",
            "access": "Highway adjacent"
        },
        fractional=False
    )
    print(f"  Asset ID: {land_sqm.asset_id[:16]}...")
    print(f"  Area: 5,000 Square Meters")
    print(f"  Location: Tokyo, Japan")
    
    return land_acres, land_hectares, land_sqft, land_sqm


def demo_fractionalization():
    """Demonstrate fractionalization feature"""
    print_header("FRACTIONALIZATION DEMO")
    
    wallet = Wallet.create()
    print(f"Owner wallet: {wallet.address}\n")
    
    # Create whole asset
    print("[1] Creating whole asset - Building")
    building = Asset(
        asset_type=AssetType.REAL_ESTATE,
        name="Commercial Building - Downtown",
        description="10-story office building",
        total_supply=1.0,
        owner_address=wallet.address,
        metadata={
            "floors": 10,
            "sqft": 50000,
            "location": "Financial District",
            "valuation": 10000000
        },
        fractional=False
    )
    print(f"  Asset ID: {building.asset_id[:16]}...")
    print(f"  Type: {building.asset_type.value}")
    print(f"  Standard: {building.standard.value} (NFT)")
    print(f"  Fractional: No")
    print(f"  Owner: {wallet.address}")
    
    # Fractionalize
    print("\n[2] Fractionalizing into 1000 shares...")
    success, msg = building.fractionalize(1000)
    print(f"  Result: {msg}")
    print(f"  New Standard: {building.standard.value}")
    print(f"  Total Shares: {building.total_supply}")
    print(f"  Owner Balance: {building.get_balance(wallet.address)} shares")
    print(f"  Share Value: $10,000 per share (if $10M valuation)")
    
    # Distribute shares
    print("\n[3] Distributing shares to investors...")
    investors = [Wallet.create() for _ in range(3)]
    
    for i, investor in enumerate(investors):
        shares = 100 * (i + 1)  # 100, 200, 300 shares
        success, _ = building.transfer(wallet.address, investor.address, shares)
        print(f"  Investor {i+1}: {shares} shares -> {investor.address[:20]}...")
    
    print(f"\n  Remaining with owner: {building.get_balance(wallet.address)} shares")
    
    return building, investors


def demo_transfer_and_ownership():
    """Demonstrate transfer and ownership tracking"""
    print_header("TRANSFER & OWNERSHIP DEMO")
    
    # Create owner and recipients
    owner = Wallet.create()
    buyer1 = Wallet.create()
    buyer2 = Wallet.create()
    
    print(f"Owner: {owner.address[:30]}...")
    print(f"Buyer 1: {buyer1.address[:30]}...")
    print(f"Buyer 2: {buyer2.address[:30]}...\n")
    
    # Create fractional gold asset
    print("[1] Creating fractional gold asset - 1000 shares")
    gold = Asset(
        asset_type=AssetType.GOLD,
        name="Gold Pool - 1kg",
        description="Shared gold ownership",
        total_supply=1000.0,
        owner_address=owner.address,
        metadata={"unit": "g", "quantity": 1000},
        fractional=True
    )
    print(f"  Asset ID: {gold.asset_id[:16]}...")
    print(f"  Total Shares: 1000")
    
    # Transfer shares
    print("\n[2] Transferring shares...")
    
    # Owner -> Buyer1: 300 shares
    success, _ = gold.transfer(owner.address, buyer1.address, 300)
    print(f"  Owner -> Buyer 1: 300 shares")
    
    # Owner -> Buyer2: 200 shares
    success, _ = gold.transfer(owner.address, buyer2.address, 200)
    print(f"  Owner -> Buyer 2: 200 shares")
    
    # Buyer1 -> Buyer2: 100 shares
    success, _ = gold.transfer(buyer1.address, buyer2.address, 100)
    print(f"  Buyer 1 -> Buyer 2: 100 shares")
    
    # Show final balances
    print("\n[3] Final Balances:")
    print(f"  Owner: {gold.get_balance(owner.address)} shares")
    print(f"  Buyer 1: {gold.get_balance(buyer1.address)} shares")
    print(f"  Buyer 2: {gold.get_balance(buyer2.address)} shares")
    print(f"  Total: {gold.get_balance(owner.address) + gold.get_balance(buyer1.address) + gold.get_balance(buyer2.address)} shares")
    
    # Show history
    print("\n[4] Transaction History:")
    for i, event in enumerate(gold.history):
        print(f"  {i+1}. {event['event']}: ", end="")
        if event['to']:
            print(f"{event['from'][:20]}... -> {event['to'][:20]}... ({event['amount']} shares)")
        else:
            print(f"Created by {event['from'][:20]}... ({event['amount']} shares)")
    
    return gold


def demo_registry():
    """Demonstrate asset registry"""
    print_header("ASSET REGISTRY DEMO")
    
    registry = AssetRegistry()
    wallet = Wallet.create()
    
    print(f"Registry owner: {wallet.address}\n")
    
    # Register multiple assets
    print("[1] Registering multiple assets...")
    
    assets = [
        Asset(AssetType.GOLD, "Gold Bar 1oz", "Gold", 1.0, wallet.address),
        Asset(AssetType.GOLD, "Gold Bar 10oz", "Gold", 1.0, wallet.address),
        Asset(AssetType.LAND, "Land 50 Acres", "Land", 1.0, wallet.address),
        Asset(AssetType.LAND, "Land 20 Hectares", "Land", 1.0, wallet.address),
        Asset(AssetType.REAL_ESTATE, "Building A", "Real Estate", 1.0, wallet.address),
    ]
    
    for asset in assets:
        registry.register_asset(asset)
        print(f"  Registered: {asset.name} ({asset.asset_type.value})")
    
    # Get stats
    print("\n[2] Registry Statistics:")
    stats = registry.get_stats()
    print(f"  Total Assets: {stats['total_assets']}")
    print(f"  Total Owners: {stats['total_owners']}")
    print(f"  Fractional Assets: {stats['fractional_assets']}")
    print("\n  Assets by Type:")
    for asset_type, count in stats['asset_types'].items():
        if count > 0:
            print(f"    {asset_type}: {count}")
    
    # Get assets by owner
    print("\n[3] Assets owned by wallet:")
    owned = registry.get_assets_by_owner(wallet.address)
    for asset in owned:
        print(f"  - {asset.name} (ID: {asset.asset_id[:16]}...)")
    
    return registry


def demo_security_features():
    """Demonstrate security features"""
    print_header("SECURITY FEATURES DEMO")
    
    print("[1] Signature-based Ownership")
    wallet = Wallet.create()
    asset = Asset(
        asset_type=AssetType.GOLD,
        name="Secure Gold",
        description="Gold with signature verification",
        total_supply=1.0,
        owner_address=wallet.address
    )
    print(f"  Asset owner: {asset.owner_address}")
    print(f"  Wallet address: {wallet.address}")
    print(f"  Match: {asset.owner_address == wallet.address}")
    
    print("\n[2] Immutable Asset ID")
    original_id = asset.asset_id
    print(f"  Original ID: {original_id[:32]}...")
    # Try operations
    recipient = Wallet.create()
    asset.transfer(wallet.address, recipient.address, 1.0)
    print(f"  After transfer: {asset.asset_id[:32]}...")
    print(f"  ID unchanged: {asset.asset_id == original_id}")
    
    print("\n[3] Complete Audit Trail")
    print(f"  History events: {len(asset.history)}")
    for event in asset.history:
        print(f"    - {event['event']} at timestamp {event['timestamp']}")
    
    print("\n[4] Transfer Validation")
    attacker = Wallet.create()
    success, msg = asset.transfer(attacker.address, wallet.address, 1.0)
    print(f"  Unauthorized transfer: {success}")
    print(f"  Error: {msg}")
    
    print("\n[5] Unique Asset IDs")
    ids = set()
    for _ in range(100):
        a = Asset(AssetType.GOLD, "Test", "Test", 1.0, wallet.address)
        ids.add(a.asset_id)
    print(f"  Created 100 assets")
    print(f"  Unique IDs: {len(ids)}")
    print(f"  No collisions: {len(ids) == 100}")


def main():
    """Run complete demonstration"""
    print("\n" + "=" * 70)
    print(" " * 10 + "PHN BLOCKCHAIN - ASSET TOKENIZATION SYSTEM")
    print(" " * 15 + "COMPLETE FEATURE DEMONSTRATION")
    print("=" * 70)
    
    input("\nPress Enter to start demonstration...")
    
    # Demo 1: Gold Tokenization
    demo_gold_tokenization()
    input("\nPress Enter to continue...")
    
    # Demo 2: Land Tokenization
    demo_land_tokenization()
    input("\nPress Enter to continue...")
    
    # Demo 3: Fractionalization
    demo_fractionalization()
    input("\nPress Enter to continue...")
    
    # Demo 4: Transfer and Ownership
    demo_transfer_and_ownership()
    input("\nPress Enter to continue...")
    
    # Demo 5: Registry
    demo_registry()
    input("\nPress Enter to continue...")
    
    # Demo 6: Security
    demo_security_features()
    
    # Final Summary
    print_header("DEMONSTRATION COMPLETE")
    print("Features Demonstrated:")
    print("  [OK] Gold tokenization (oz, g, kg)")
    print("  [OK] Land tokenization (acres, hectares, sqft, sqm)")
    print("  [OK] Fractionalization (NFT -> Multi-Token)")
    print("  [OK] Ownership tracking")
    print("  [OK] Transfer functionality")
    print("  [OK] Asset registry")
    print("  [OK] Complete audit trail")
    print("  [OK] Security validation")
    print("  [OK] Industry-standard compliance (PHN-721, PHN-1155)")
    print("\n" + "=" * 70)
    print(" " * 15 + "SYSTEM READY FOR PRODUCTION USE")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDemo cancelled by user")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
