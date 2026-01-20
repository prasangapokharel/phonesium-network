"""
Create Tokenized Assets - PHN Blockchain
User-friendly tool for creating gold, land, and custom assets

Features:
- Gold tokenization (ounces, grams, kilograms)
- Land tokenization (acres, hectares, sqft, sqm)
- Custom asset creation
- Fractionalization support
- Secure signature-based ownership
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.assets import Asset, AssetType, AssetRegistry, asset_registry, AssetTransaction
from phonesium import Wallet
import orjson


def print_header():
    print("\n" + "=" * 70)
    print(" " * 15 + "PHN BLOCKCHAIN - ASSET TOKENIZATION")
    print("=" * 70)
    print("\nCreate tokenized assets backed by real-world value")
    print("- Gold (ounces, grams, kilograms)")
    print("- Land (acres, hectares, square feet, square meters)")
    print("- Real Estate (properties, buildings)")
    print("- Custom Assets (anything you want to tokenize)")
    print("=" * 70 + "\n")


def create_gold_asset():
    """Create tokenized gold asset"""
    print("\n" + "-" * 70)
    print("CREATE GOLD ASSET")
    print("-" * 70)
    
    # Get gold details
    print("\nGold Details:")
    name = input("  Asset Name (e.g., 'Premium Gold Bar 100oz'): ").strip()
    
    print("\n  Select Unit:")
    print("  1. Troy Ounces (oz)")
    print("  2. Grams (g)")
    print("  3. Kilograms (kg)")
    unit_choice = input("  Choice [1-3]: ").strip()
    
    units = {
        "1": ("troy_oz", "Troy Ounces"),
        "2": ("g", "Grams"),
        "3": ("kg", "Kilograms")
    }
    
    unit_key, unit_name = units.get(unit_choice, ("troy_oz", "Troy Ounces"))
    
    try:
        quantity = float(input(f"  Quantity ({unit_name}): ").strip())
    except ValueError:
        print("[ERROR] Invalid quantity")
        return None
    
    purity = input("  Purity (e.g., '99.99%', '24K'): ").strip()
    serial_number = input("  Serial Number (optional): ").strip()
    certificate = input("  Certificate ID (optional): ").strip()
    vault_location = input("  Vault/Storage Location: ").strip()
    
    description = f"{quantity} {unit_name} of Gold, Purity: {purity}"
    if serial_number:
        description += f", Serial: {serial_number}"
    
    # Fractionalization
    print("\n  Fractionalization:")
    fractional_input = input("  Make fractional? (y/n) [n]: ").strip().lower()
    fractional = fractional_input == 'y'
    
    total_supply = 1.0
    if fractional:
        try:
            total_supply = float(input("  Number of fractions/shares: ").strip())
        except ValueError:
            print("[WARN] Invalid number, using 1")
            total_supply = 1.0
    
    # Load wallet
    print("\n  Owner Wallet:")
    wallet_path = input("  Wallet file path: ").strip()
    password = input("  Wallet password: ").strip()
    
    try:
        wallet = Wallet.load(wallet_path, password)
        print(f"  [OK] Wallet loaded: {wallet.address}")
    except Exception as e:
        print(f"  [ERROR] Failed to load wallet: {e}")
        return None
    
    # Create asset
    metadata = {
        "unit": unit_key,
        "quantity": quantity,
        "purity": purity,
        "serial_number": serial_number,
        "certificate": certificate,
        "vault_location": vault_location,
        "verification_date": None,
        "insured": False
    }
    
    asset = Asset(
        asset_type=AssetType.GOLD,
        name=name,
        description=description,
        total_supply=total_supply,
        owner_address=wallet.address,
        metadata=metadata,
        fractional=fractional
    )
    
    # Register asset
    success, msg = asset_registry.register_asset(asset)
    
    if success:
        print(f"\n[OK] GOLD ASSET CREATED SUCCESSFULLY!")
        print(f"  Asset ID: {asset.asset_id}")
        print(f"  Type: {asset.asset_type.value}")
        print(f"  Name: {asset.name}")
        print(f"  Quantity: {quantity} {unit_name}")
        print(f"  Purity: {purity}")
        print(f"  Owner: {wallet.address}")
        print(f"  Fractional: {'Yes' if fractional else 'No'}")
        if fractional:
            print(f"  Total Shares: {total_supply}")
        
        # Save to file
        save_path = f"user/assets/gold_{asset.asset_id[:8]}.json"
        os.makedirs("user/assets", exist_ok=True)
        
        with open(save_path, 'w') as f:
            f.write(orjson.dumps(asset.to_dict(), option=orjson.OPT_INDENT_2))
        
        print(f"\n  Asset saved to: {save_path}")
        
        return asset
    else:
        print(f"\n[ERROR] {msg}")
        return None


def create_land_asset():
    """Create tokenized land asset"""
    print("\n" + "-" * 70)
    print("CREATE LAND ASSET")
    print("-" * 70)
    
    # Get land details
    print("\nLand Details:")
    name = input("  Asset Name (e.g., 'Prime Agricultural Land - 50 Acres'): ").strip()
    
    print("\n  Select Unit:")
    print("  1. Acres")
    print("  2. Hectares")
    print("  3. Square Feet (sqft)")
    print("  4. Square Meters (sqm)")
    unit_choice = input("  Choice [1-4]: ").strip()
    
    units = {
        "1": ("acres", "Acres"),
        "2": ("hectares", "Hectares"),
        "3": ("sqft", "Square Feet"),
        "4": ("sqm", "Square Meters")
    }
    
    unit_key, unit_name = units.get(unit_choice, ("acres", "Acres"))
    
    try:
        area = float(input(f"  Area ({unit_name}): ").strip())
    except ValueError:
        print("[ERROR] Invalid area")
        return None
    
    location = input("  Location (Address/Coordinates): ").strip()
    land_use = input("  Land Use (Agricultural/Residential/Commercial): ").strip()
    deed_number = input("  Deed/Title Number: ").strip()
    parcel_id = input("  Parcel ID (optional): ").strip()
    zoning = input("  Zoning Classification: ").strip()
    
    description = f"{area} {unit_name} of Land, Location: {location}, Use: {land_use}"
    
    # Fractionalization
    print("\n  Fractionalization:")
    fractional_input = input("  Make fractional? (y/n) [n]: ").strip().lower()
    fractional = fractional_input == 'y'
    
    total_supply = 1.0
    if fractional:
        try:
            total_supply = float(input("  Number of fractions/shares: ").strip())
        except ValueError:
            total_supply = 1.0
    
    # Load wallet
    print("\n  Owner Wallet:")
    wallet_path = input("  Wallet file path: ").strip()
    password = input("  Wallet password: ").strip()
    
    try:
        wallet = Wallet.load(wallet_path, password)
        print(f"  [OK] Wallet loaded: {wallet.address}")
    except Exception as e:
        print(f"  [ERROR] Failed to load wallet: {e}")
        return None
    
    # Create asset
    metadata = {
        "unit": unit_key,
        "area": area,
        "location": location,
        "land_use": land_use,
        "deed_number": deed_number,
        "parcel_id": parcel_id,
        "zoning": zoning,
        "surveyed": False,
        "encumbrances": []
    }
    
    asset = Asset(
        asset_type=AssetType.LAND,
        name=name,
        description=description,
        total_supply=total_supply,
        owner_address=wallet.address,
        metadata=metadata,
        fractional=fractional
    )
    
    # Register asset
    success, msg = asset_registry.register_asset(asset)
    
    if success:
        print(f"\n[OK] LAND ASSET CREATED SUCCESSFULLY!")
        print(f"  Asset ID: {asset.asset_id}")
        print(f"  Type: {asset.asset_type.value}")
        print(f"  Name: {asset.name}")
        print(f"  Area: {area} {unit_name}")
        print(f"  Location: {location}")
        print(f"  Owner: {wallet.address}")
        print(f"  Fractional: {'Yes' if fractional else 'No'}")
        if fractional:
            print(f"  Total Shares: {total_supply}")
        
        # Save to file
        save_path = f"user/assets/land_{asset.asset_id[:8]}.json"
        os.makedirs("user/assets", exist_ok=True)
        
        with open(save_path, 'w') as f:
            f.write(orjson.dumps(asset.to_dict(), option=orjson.OPT_INDENT_2))
        
        print(f"\n  Asset saved to: {save_path}")
        
        return asset
    else:
        print(f"\n[ERROR] {msg}")
        return None


def create_custom_asset():
    """Create custom tokenized asset"""
    print("\n" + "-" * 70)
    print("CREATE CUSTOM ASSET")
    print("-" * 70)
    
    print("\nAsset Details:")
    name = input("  Asset Name: ").strip()
    description = input("  Description: ").strip()
    
    print("\n  Select Asset Type:")
    print("  1. Gold")
    print("  2. Land")
    print("  3. Real Estate")
    print("  4. Commodity")
    print("  5. Security")
    print("  6. Custom")
    type_choice = input("  Choice [1-6]: ").strip()
    
    types = {
        "1": AssetType.GOLD,
        "2": AssetType.LAND,
        "3": AssetType.REAL_ESTATE,
        "4": AssetType.COMMODITY,
        "5": AssetType.SECURITY,
        "6": AssetType.CUSTOM
    }
    
    asset_type = types.get(type_choice, AssetType.CUSTOM)
    
    # Custom metadata
    print("\n  Custom Metadata (key=value, one per line, empty line to finish):")
    metadata = {}
    while True:
        line = input("  ").strip()
        if not line:
            break
        if '=' in line:
            key, value = line.split('=', 1)
            metadata[key.strip()] = value.strip()
    
    # Fractionalization
    fractional_input = input("\n  Make fractional? (y/n) [n]: ").strip().lower()
    fractional = fractional_input == 'y'
    
    total_supply = 1.0
    if fractional:
        try:
            total_supply = float(input("  Number of fractions/shares: ").strip())
        except ValueError:
            total_supply = 1.0
    
    # Load wallet
    print("\n  Owner Wallet:")
    wallet_path = input("  Wallet file path: ").strip()
    password = input("  Wallet password: ").strip()
    
    try:
        wallet = Wallet.load(wallet_path, password)
        print(f"  [OK] Wallet loaded: {wallet.address}")
    except Exception as e:
        print(f"  [ERROR] Failed to load wallet: {e}")
        return None
    
    # Create asset
    asset = Asset(
        asset_type=asset_type,
        name=name,
        description=description,
        total_supply=total_supply,
        owner_address=wallet.address,
        metadata=metadata,
        fractional=fractional
    )
    
    # Register asset
    success, msg = asset_registry.register_asset(asset)
    
    if success:
        print(f"\n[OK] CUSTOM ASSET CREATED SUCCESSFULLY!")
        print(f"  Asset ID: {asset.asset_id}")
        print(f"  Type: {asset.asset_type.value}")
        print(f"  Name: {asset.name}")
        print(f"  Owner: {wallet.address}")
        print(f"  Fractional: {'Yes' if fractional else 'No'}")
        if fractional:
            print(f"  Total Shares: {total_supply}")
        
        # Save to file
        save_path = f"user/assets/custom_{asset.asset_id[:8]}.json"
        os.makedirs("user/assets", exist_ok=True)
        
        with open(save_path, 'w') as f:
            f.write(orjson.dumps(asset.to_dict(), option=orjson.OPT_INDENT_2))
        
        print(f"\n  Asset saved to: {save_path}")
        
        return asset
    else:
        print(f"\n[ERROR] {msg}")
        return None


def main():
    print_header()
    
    while True:
        print("\nSelect Asset Type to Create:")
        print("  1. Gold (ounces, grams, kg)")
        print("  2. Land (acres, hectares, sqft, sqm)")
        print("  3. Custom Asset")
        print("  4. View Asset Registry")
        print("  5. Exit")
        
        choice = input("\nChoice [1-5]: ").strip()
        
        if choice == "1":
            create_gold_asset()
        elif choice == "2":
            create_land_asset()
        elif choice == "3":
            create_custom_asset()
        elif choice == "4":
            stats = asset_registry.get_stats()
            print("\n" + "-" * 70)
            print("ASSET REGISTRY STATISTICS")
            print("-" * 70)
            print(f"  Total Assets: {stats['total_assets']}")
            print(f"  Total Owners: {stats['total_owners']}")
            print(f"  Fractional Assets: {stats['fractional_assets']}")
            print("\n  Assets by Type:")
            for asset_type, count in stats['asset_types'].items():
                if count > 0:
                    print(f"    {asset_type}: {count}")
        elif choice == "5":
            print("\nGoodbye!")
            break
        else:
            print("\n[ERROR] Invalid choice")
        
        input("\nPress Enter to continue...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
    except Exception as e:
        print(f"\n[ERROR] {e}")
