"""
Comprehensive Asset Tokenization Tests
Tests all features, security, and flexibility
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.assets.tokenization import Asset, AssetType, AssetRegistry, AssetStandard, AssetTransaction
from phonesium import Wallet
import pytest


class TestAssetCreation:
    """Test asset creation with different types"""
    
    def test_create_gold_asset(self):
        """Test creating gold asset"""
        wallet = Wallet.create()
        
        asset = Asset(
            asset_type=AssetType.GOLD,
            name="100oz Gold Bar",
            description="Premium gold bar, 99.99% purity",
            total_supply=1.0,
            owner_address=wallet.address,
            metadata={
                "unit": "troy_oz",
                "quantity": 100,
                "purity": "99.99%",
                "serial": "GB-2024-001"
            },
            fractional=False
        )
        
        assert asset.asset_type == AssetType.GOLD
        assert asset.name == "100oz Gold Bar"
        assert asset.total_supply == 1.0
        assert asset.owner_address == wallet.address
        assert not asset.fractional
        assert asset.standard == AssetStandard.PHN721
        print(f"[OK] Gold asset created: {asset.asset_id[:8]}...")
    
    def test_create_land_asset(self):
        """Test creating land asset"""
        wallet = Wallet.create()
        
        asset = Asset(
            asset_type=AssetType.LAND,
            name="50 Acres Agricultural Land",
            description="Prime farmland in Iowa",
            total_supply=1.0,
            owner_address=wallet.address,
            metadata={
                "unit": "acres",
                "area": 50,
                "location": "Iowa, USA",
                "deed": "DEED-2024-001",
                "zoning": "Agricultural"
            },
            fractional=False
        )
        
        assert asset.asset_type == AssetType.LAND
        assert asset.name == "50 Acres Agricultural Land"
        assert asset.metadata["area"] == 50
        print(f"[OK] Land asset created: {asset.asset_id[:8]}...")
    
    def test_create_fractional_asset(self):
        """Test creating fractional asset"""
        wallet = Wallet.create()
        
        asset = Asset(
            asset_type=AssetType.GOLD,
            name="Gold Pool - 1000oz",
            description="Shared gold pool",
            total_supply=1000.0,  # 1000 shares
            owner_address=wallet.address,
            metadata={"unit": "troy_oz", "quantity": 1000},
            fractional=True,
            standard=AssetStandard.PHN1155
        )
        
        assert asset.fractional
        assert asset.total_supply == 1000.0
        assert asset.standard == AssetStandard.PHN1155
        assert asset.get_balance(wallet.address) == 1000.0
        print(f"[OK] Fractional asset created with 1000 shares")
    
    def test_create_custom_asset(self):
        """Test creating custom asset type"""
        wallet = Wallet.create()
        
        asset = Asset(
            asset_type=AssetType.CUSTOM,
            name="Vintage Wine Collection",
            description="Rare wines from 1945",
            total_supply=1.0,
            owner_address=wallet.address,
            metadata={
                "bottles": 24,
                "vintage": "1945",
                "origin": "Bordeaux, France",
                "appraised_value": 50000
            },
            fractional=False
        )
        
        assert asset.asset_type == AssetType.CUSTOM
        assert asset.metadata["bottles"] == 24
        print(f"[OK] Custom asset created")


class TestAssetTransfer:
    """Test asset transfer functionality"""
    
    def test_transfer_whole_asset(self):
        """Test transferring entire non-fractional asset"""
        owner = Wallet.create()
        recipient = Wallet.create()
        
        asset = Asset(
            asset_type=AssetType.GOLD,
            name="Gold Bar",
            description="100oz gold",
            total_supply=1.0,
            owner_address=owner.address,
            fractional=False
        )
        
        # Transfer
        success, msg = asset.transfer(owner.address, recipient.address, 1.0)
        
        assert success
        assert asset.get_balance(owner.address) == 0.0
        assert asset.get_balance(recipient.address) == 1.0
        assert len(asset.history) == 2  # Creation + Transfer
        print(f"[OK] Whole asset transferred successfully")
    
    def test_transfer_fractional_asset(self):
        """Test transferring fractions"""
        owner = Wallet.create()
        recipient1 = Wallet.create()
        recipient2 = Wallet.create()
        
        asset = Asset(
            asset_type=AssetType.LAND,
            name="100 Acre Land",
            description="Shared ownership",
            total_supply=100.0,
            owner_address=owner.address,
            fractional=True,
            standard=AssetStandard.PHN1155
        )
        
        # Transfer 30 shares to recipient1
        success1, _ = asset.transfer(owner.address, recipient1.address, 30.0)
        assert success1
        assert asset.get_balance(owner.address) == 70.0
        assert asset.get_balance(recipient1.address) == 30.0
        
        # Transfer 20 shares to recipient2
        success2, _ = asset.transfer(owner.address, recipient2.address, 20.0)
        assert success2
        assert asset.get_balance(owner.address) == 50.0
        assert asset.get_balance(recipient2.address) == 20.0
        
        print(f"[OK] Fractional transfers: 30 + 20 shares")
    
    def test_transfer_insufficient_balance(self):
        """Test transfer with insufficient balance fails"""
        owner = Wallet.create()
        recipient = Wallet.create()
        
        asset = Asset(
            asset_type=AssetType.GOLD,
            name="Gold",
            description="Test",
            total_supply=10.0,
            owner_address=owner.address,
            fractional=True
        )
        
        # Try to transfer more than balance
        success, msg = asset.transfer(owner.address, recipient.address, 20.0)
        
        assert not success
        assert "Insufficient" in msg
        print(f"[OK] Insufficient balance transfer rejected")
    
    def test_partial_nonfractional_fails(self):
        """Test partial transfer of non-fractional asset fails"""
        owner = Wallet.create()
        recipient = Wallet.create()
        
        asset = Asset(
            asset_type=AssetType.LAND,
            name="Property",
            description="Single property",
            total_supply=1.0,
            owner_address=owner.address,
            fractional=False
        )
        
        # Try partial transfer
        success, msg = asset.transfer(owner.address, recipient.address, 0.5)
        
        assert not success
        assert "whole" in msg.lower()
        print(f"[OK] Partial non-fractional transfer rejected")


class TestFractionalization:
    """Test asset fractionalization"""
    
    def test_fractionalize_asset(self):
        """Test converting whole asset to fractions"""
        wallet = Wallet.create()
        
        asset = Asset(
            asset_type=AssetType.REAL_ESTATE,
            name="Building",
            description="Commercial building",
            total_supply=1.0,
            owner_address=wallet.address,
            fractional=False
        )
        
        # Fractionalize into 100 shares
        success, msg = asset.fractionalize(100)
        
        assert success
        assert asset.fractional
        assert asset.total_supply == 100.0
        assert asset.get_balance(wallet.address) == 100.0
        assert asset.standard == AssetStandard.PHN1155
        print(f"[OK] Asset fractionalized into 100 shares")
    
    def test_fractionalize_already_fractional(self):
        """Test fractionalizing already fractional asset fails"""
        wallet = Wallet.create()
        
        asset = Asset(
            asset_type=AssetType.GOLD,
            name="Gold",
            description="Test",
            total_supply=10.0,
            owner_address=wallet.address,
            fractional=True
        )
        
        success, msg = asset.fractionalize(20)
        
        assert not success
        assert "already" in msg.lower()
        print(f"[OK] Double fractionalization rejected")
    
    def test_fractionalize_invalid_number(self):
        """Test fractionalization with invalid number fails"""
        wallet = Wallet.create()
        
        asset = Asset(
            asset_type=AssetType.LAND,
            name="Land",
            description="Test",
            total_supply=1.0,
            owner_address=wallet.address,
            fractional=False
        )
        
        success, msg = asset.fractionalize(1)
        
        assert not success
        assert "at least 2" in msg.lower()
        print(f"[OK] Invalid fractionalization rejected")


class TestAssetRegistry:
    """Test asset registry functionality"""
    
    def test_register_asset(self):
        """Test registering asset in registry"""
        registry = AssetRegistry()
        wallet = Wallet.create()
        
        asset = Asset(
            asset_type=AssetType.GOLD,
            name="Gold",
            description="Test gold",
            total_supply=1.0,
            owner_address=wallet.address
        )
        
        success, msg = registry.register_asset(asset)
        
        assert success
        assert asset.asset_id in registry.assets
        assert wallet.address in registry.owner_assets
        print(f"[OK] Asset registered in registry")
    
    def test_get_asset_by_id(self):
        """Test retrieving asset by ID"""
        registry = AssetRegistry()
        wallet = Wallet.create()
        
        asset = Asset(
            asset_type=AssetType.LAND,
            name="Land",
            description="Test",
            total_supply=1.0,
            owner_address=wallet.address
        )
        
        registry.register_asset(asset)
        retrieved = registry.get_asset(asset.asset_id)
        
        assert retrieved is not None
        assert retrieved.asset_id == asset.asset_id
        assert retrieved.name == asset.name
        print(f"[OK] Asset retrieved by ID")
    
    def test_get_assets_by_owner(self):
        """Test getting all assets owned by address"""
        registry = AssetRegistry()
        wallet = Wallet.create()
        
        # Create multiple assets
        for i in range(3):
            asset = Asset(
                asset_type=AssetType.GOLD,
                name=f"Gold {i}",
                description=f"Test {i}",
                total_supply=1.0,
                owner_address=wallet.address
            )
            registry.register_asset(asset)
        
        owned = registry.get_assets_by_owner(wallet.address)
        
        assert len(owned) == 3
        print(f"[OK] Retrieved {len(owned)} assets by owner")
    
    def test_registry_transfer(self):
        """Test transferring asset through registry"""
        registry = AssetRegistry()
        owner = Wallet.create()
        recipient = Wallet.create()
        
        asset = Asset(
            asset_type=AssetType.GOLD,
            name="Gold",
            description="Test",
            total_supply=10.0,
            owner_address=owner.address,
            fractional=True
        )
        
        registry.register_asset(asset)
        
        # Transfer through registry
        success, msg = registry.transfer_asset(
            asset.asset_id, 
            owner.address, 
            recipient.address, 
            5.0
        )
        
        assert success
        assert registry.get_asset_balance(asset.asset_id, owner.address) == 5.0
        assert registry.get_asset_balance(asset.asset_id, recipient.address) == 5.0
        print(f"[OK] Asset transferred through registry")


class TestAssetSecurity:
    """Test security features"""
    
    def test_asset_history_tracking(self):
        """Test complete history is tracked"""
        owner = Wallet.create()
        recipient = Wallet.create()
        
        asset = Asset(
            asset_type=AssetType.GOLD,
            name="Gold",
            description="Test",
            total_supply=10.0,
            owner_address=owner.address,
            fractional=True
        )
        
        # Make transfers
        asset.transfer(owner.address, recipient.address, 3.0)
        asset.transfer(recipient.address, owner.address, 1.0)
        
        # Check history
        assert len(asset.history) == 3  # Create + 2 transfers
        assert asset.history[0]["event"] == "CREATED"
        assert asset.history[1]["event"] == "TRANSFER"
        assert asset.history[2]["event"] == "TRANSFER"
        print(f"[OK] Complete history tracked: {len(asset.history)} events")
    
    def test_asset_immutability(self):
        """Test asset ID is immutable"""
        wallet = Wallet.create()
        
        asset = Asset(
            asset_type=AssetType.LAND,
            name="Land",
            description="Test",
            total_supply=1.0,
            owner_address=wallet.address
        )
        
        original_id = asset.asset_id
        
        # Try to change (should not affect asset_id)
        asset.transfer(wallet.address, Wallet.create().address, 1.0)
        
        assert asset.asset_id == original_id
        print(f"[OK] Asset ID remains immutable")
    
    def test_unique_asset_ids(self):
        """Test all asset IDs are unique"""
        wallet = Wallet.create()
        ids = set()
        
        for _ in range(100):
            asset = Asset(
                asset_type=AssetType.GOLD,
                name="Test",
                description="Test",
                total_supply=1.0,
                owner_address=wallet.address
            )
            ids.add(asset.asset_id)
        
        assert len(ids) == 100
        print(f"[OK] All 100 asset IDs are unique")


class TestAssetFlexibility:
    """Test system flexibility with various scenarios"""
    
    def test_gold_ounces(self):
        """Test gold in troy ounces"""
        wallet = Wallet.create()
        asset = Asset(
            asset_type=AssetType.GOLD,
            name="Gold - 100 Troy Ounces",
            description="100oz gold bar",
            total_supply=100.0,
            owner_address=wallet.address,
            metadata={"unit": "troy_oz", "quantity": 100},
            fractional=True
        )
        assert asset.metadata["unit"] == "troy_oz"
        print("[OK] Gold in troy ounces")
    
    def test_gold_grams(self):
        """Test gold in grams"""
        wallet = Wallet.create()
        asset = Asset(
            asset_type=AssetType.GOLD,
            name="Gold - 1000 Grams",
            description="1kg gold",
            total_supply=1000.0,
            owner_address=wallet.address,
            metadata={"unit": "g", "quantity": 1000},
            fractional=True
        )
        assert asset.metadata["unit"] == "g"
        print("[OK] Gold in grams")
    
    def test_land_acres(self):
        """Test land in acres"""
        wallet = Wallet.create()
        asset = Asset(
            asset_type=AssetType.LAND,
            name="50 Acres Land",
            description="Farmland",
            total_supply=1.0,
            owner_address=wallet.address,
            metadata={"unit": "acres", "area": 50}
        )
        assert asset.metadata["unit"] == "acres"
        print("[OK] Land in acres")
    
    def test_land_hectares(self):
        """Test land in hectares"""
        wallet = Wallet.create()
        asset = Asset(
            asset_type=AssetType.LAND,
            name="20 Hectares Land",
            description="Farmland",
            total_supply=1.0,
            owner_address=wallet.address,
            metadata={"unit": "hectares", "area": 20}
        )
        assert asset.metadata["unit"] == "hectares"
        print("[OK] Land in hectares")
    
    def test_mixed_asset_types(self):
        """Test registry with multiple asset types"""
        registry = AssetRegistry()
        wallet = Wallet.create()
        
        # Create various assets
        assets = [
            Asset(AssetType.GOLD, "Gold", "Gold asset", 1.0, wallet.address),
            Asset(AssetType.LAND, "Land", "Land asset", 1.0, wallet.address),
            Asset(AssetType.REAL_ESTATE, "Building", "Real estate", 1.0, wallet.address),
            Asset(AssetType.COMMODITY, "Oil", "Commodity", 1.0, wallet.address),
            Asset(AssetType.CUSTOM, "Art", "Custom asset", 1.0, wallet.address)
        ]
        
        for asset in assets:
            registry.register_asset(asset)
        
        stats = registry.get_stats()
        assert stats["total_assets"] == 5
        print(f"[OK] Mixed assets: {stats['total_assets']} different types")


def run_all_tests():
    """Run all tests manually"""
    print("\n" + "=" * 70)
    print(" " * 15 + "ASSET TOKENIZATION - COMPREHENSIVE TESTS")
    print("=" * 70 + "\n")
    
    test_classes = [
        TestAssetCreation,
        TestAssetTransfer,
        TestFractionalization,
        TestAssetRegistry,
        TestAssetSecurity,
        TestAssetFlexibility
    ]
    
    total_tests = 0
    passed_tests = 0
    
    for test_class in test_classes:
        print(f"\n{test_class.__name__}:")
        print("-" * 70)
        
        test_instance = test_class()
        test_methods = [m for m in dir(test_instance) if m.startswith('test_')]
        
        for method_name in test_methods:
            total_tests += 1
            try:
                method = getattr(test_instance, method_name)
                method()
                passed_tests += 1
            except Exception as e:
                print(f"[FAIL] {method_name}: {e}")
    
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
    print("=" * 70 + "\n")
    
    return passed_tests == total_tests


if __name__ == "__main__":
    import sys
    
    # Can be run with pytest or directly
    if 'pytest' in sys.modules:
        # Running with pytest
        pytest.main([__file__, "-v", "--tb=short"])
    else:
        # Running directly
        success = run_all_tests()
        sys.exit(0 if success else 1)
