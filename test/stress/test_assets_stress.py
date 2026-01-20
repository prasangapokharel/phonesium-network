"""
MILITARY-GRADE ASSETS STRESS TESTS
Tests for real-world scenarios and edge cases in AssetCreator
"""

import sys
import time
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from phonesium import Wallet, AssetCreator, AssetType


class AssetsStressTest:
    """Comprehensive asset creation stress testing"""

    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0

    def log(self, test_name, status, message=""):
        """Log test result"""
        result = {"test": test_name, "status": status, "message": message}
        self.results.append(result)

        if status == "PASS":
            self.passed += 1
            print(f"  [PASS] {test_name}")
        else:
            self.failed += 1
            print(f"  [FAIL] {test_name}: {message}")

    def test_1_basic_asset_creator(self):
        """Test 1: Basic AssetCreator initialization"""
        print("\n[TEST 1] Basic AssetCreator Initialization")
        try:
            wallet = Wallet.create()
            creator = AssetCreator(wallet)

            assert creator.wallet.address == wallet.address
            assert hasattr(creator, "create_gold_asset")
            assert hasattr(creator, "create_land_asset")
            assert hasattr(creator, "create_custom_asset")

            self.log("Basic initialization", "PASS")
        except Exception as e:
            self.log("Basic initialization", "FAIL", str(e))

    def test_2_gold_asset_all_units(self):
        """Test 2: Create gold assets with all unit types"""
        print("\n[TEST 2] Gold Assets - All Units")
        try:
            wallet = Wallet.create()
            creator = AssetCreator(wallet)

            units = ["troy_oz", "g", "kg"]

            for unit in units:
                asset = creator.create_gold_asset(
                    name=f"Gold {unit}", quantity=100.0, unit=unit, purity="99.99%"
                )

                assert asset is not None
                assert asset["asset_type"] == "gold"
                assert asset["metadata"]["unit"] == unit
                assert asset["owner_address"] == wallet.address

            self.log("Gold assets - all units", "PASS")
        except Exception as e:
            self.log("Gold assets - all units", "FAIL", str(e))

    def test_3_land_asset_all_units(self):
        """Test 3: Create land assets with all unit types"""
        print("\n[TEST 3] Land Assets - All Units")
        try:
            wallet = Wallet.create()
            creator = AssetCreator(wallet)

            units = ["acres", "hectares", "sqft", "sqm"]

            for unit in units:
                asset = creator.create_land_asset(
                    name=f"Land {unit}", area=50.0, unit=unit, location="Test Location"
                )

                assert asset is not None
                assert asset["asset_type"] == "land"
                assert asset["metadata"]["unit"] == unit

            self.log("Land assets - all units", "PASS")
        except Exception as e:
            self.log("Land assets - all units", "FAIL", str(e))

    def test_4_fractional_assets(self):
        """Test 4: Create fractional assets"""
        print("\n[TEST 4] Fractional Assets")
        try:
            wallet = Wallet.create()
            creator = AssetCreator(wallet)

            # Fractional gold
            asset1 = creator.create_gold_asset(
                name="Fractional Gold",
                quantity=100.0,
                unit="troy_oz",
                purity="99.99%",
                fractional=True,
                total_supply=1000.0,
            )

            assert asset1["fractional"] == True
            assert asset1["total_supply"] == 1000.0

            # Fractional land
            asset2 = creator.create_land_asset(
                name="Fractional Land",
                area=100.0,
                unit="acres",
                location="California",
                fractional=True,
                total_supply=500.0,
            )

            assert asset2["fractional"] == True
            assert asset2["total_supply"] == 500.0

            self.log("Fractional assets", "PASS")
        except Exception as e:
            self.log("Fractional assets", "FAIL", str(e))

    def test_5_asset_with_all_metadata(self):
        """Test 5: Create asset with complete metadata"""
        print("\n[TEST 5] Asset With Complete Metadata")
        try:
            wallet = Wallet.create()
            creator = AssetCreator(wallet)

            asset = creator.create_gold_asset(
                name="Premium Gold Bar",
                quantity=100.0,
                unit="troy_oz",
                purity="99.99%",
                serial_number="GB-2026-001",
                certificate="CERT-001",
                vault_location="Swiss Bank Zurich",
                fractional=True,
                total_supply=100.0,
            )

            assert asset["metadata"]["serial_number"] == "GB-2026-001"
            assert asset["metadata"]["certificate"] == "CERT-001"
            assert asset["metadata"]["vault_location"] == "Swiss Bank Zurich"

            self.log("Asset with complete metadata", "PASS")
        except Exception as e:
            self.log("Asset with complete metadata", "FAIL", str(e))

    def test_6_custom_asset_types(self):
        """Test 6: Create custom assets of all types"""
        print("\n[TEST 6] Custom Asset Types")
        try:
            wallet = Wallet.create()
            creator = AssetCreator(wallet)

            asset_types = [
                AssetType.GOLD,
                AssetType.LAND,
                AssetType.REAL_ESTATE,
                AssetType.COMMODITY,
                AssetType.SECURITY,
                AssetType.CUSTOM,
            ]

            for asset_type in asset_types:
                asset = creator.create_custom_asset(
                    name=f"Test {asset_type.value}",
                    description=f"Testing {asset_type.value}",
                    asset_type=asset_type,
                    metadata={"test": "data"},
                )

                assert asset is not None
                assert asset["asset_type"] == asset_type.value

            self.log("Custom asset types", "PASS")
        except Exception as e:
            self.log("Custom asset types", "FAIL", str(e))

    def test_7_extreme_values(self):
        """Test 7: Extreme quantity/area values"""
        print("\n[TEST 7] Extreme Values")
        try:
            wallet = Wallet.create()
            creator = AssetCreator(wallet)

            # Very small quantity
            asset1 = creator.create_gold_asset(
                name="Tiny Gold", quantity=0.001, unit="g", purity="99.99%"
            )
            assert asset1["metadata"]["quantity"] == 0.001

            # Very large quantity
            asset2 = creator.create_gold_asset(
                name="Huge Gold", quantity=1000000.0, unit="kg", purity="99.99%"
            )
            assert asset2["metadata"]["quantity"] == 1000000.0

            # Zero quantity (edge case)
            asset3 = creator.create_gold_asset(
                name="Zero Gold", quantity=0.0, unit="g", purity="99.99%"
            )
            assert asset3["metadata"]["quantity"] == 0.0

            # Large fractional supply
            asset4 = creator.create_land_asset(
                name="Highly Fractionalized",
                area=100.0,
                unit="acres",
                location="Test",
                fractional=True,
                total_supply=1000000.0,
            )
            assert asset4["total_supply"] == 1000000.0

            self.log("Extreme values", "PASS")
        except Exception as e:
            self.log("Extreme values", "FAIL", str(e))

    def test_8_special_characters_in_names(self):
        """Test 8: Special characters in asset names and descriptions"""
        print("\n[TEST 8] Special Characters in Names")
        try:
            wallet = Wallet.create()
            creator = AssetCreator(wallet)

            special_names = [
                "Gold & Silver Mix",
                "Land Plot #123",
                "Asset (Premium)",
                "Test-Asset-001",
                "Asset_With_Underscores",
                "Côte d'Ivoire Gold",
                "Asset with 'quotes'",
                'Asset with "double quotes"',
            ]

            for name in special_names:
                asset = creator.create_custom_asset(
                    name=name, description="Test description", metadata={}
                )
                assert asset["name"] == name

            self.log("Special characters in names", "PASS")
        except Exception as e:
            self.log("Special characters in names", "FAIL", str(e))

    def test_9_empty_optional_fields(self):
        """Test 9: Create assets with empty optional fields"""
        print("\n[TEST 9] Empty Optional Fields")
        try:
            wallet = Wallet.create()
            creator = AssetCreator(wallet)

            # Gold with minimal info
            asset1 = creator.create_gold_asset(
                name="Minimal Gold",
                quantity=100.0,
                unit="troy_oz",
                purity="99.99%",
                serial_number="",
                certificate="",
                vault_location="",
            )
            assert asset1 is not None

            # Land with minimal info
            asset2 = creator.create_land_asset(
                name="Minimal Land",
                area=50.0,
                unit="acres",
                location="",
                land_use="",
                deed_number="",
                parcel_id="",
                zoning="",
            )
            assert asset2 is not None

            self.log("Empty optional fields", "PASS")
        except Exception as e:
            self.log("Empty optional fields", "FAIL", str(e))

    def test_10_concurrent_asset_creation(self):
        """Test 10: Create multiple assets concurrently"""
        print("\n[TEST 10] Concurrent Asset Creation")
        try:
            wallet = Wallet.create()
            creator = AssetCreator(wallet)

            assets = []
            errors = []

            def create_asset(asset_id):
                try:
                    asset = creator.create_gold_asset(
                        name=f"Gold Asset {asset_id}",
                        quantity=100.0,
                        unit="troy_oz",
                        purity="99.99%",
                    )
                    assets.append(asset)
                except Exception as e:
                    errors.append(e)

            # Create 50 assets concurrently
            threads = []
            for i in range(50):
                t = threading.Thread(target=create_asset, args=(i,))
                threads.append(t)
                t.start()

            for t in threads:
                t.join(timeout=5)

            # All should have unique IDs
            asset_ids = [a["asset_id"] for a in assets]
            assert len(asset_ids) == len(set(asset_ids)), "Duplicate asset IDs found"

            self.log("Concurrent asset creation", "PASS")
        except Exception as e:
            self.log("Concurrent asset creation", "FAIL", str(e))

    def test_11_rapid_asset_creation(self):
        """Test 11: Create many assets rapidly"""
        print("\n[TEST 11] Rapid Asset Creation")
        try:
            wallet = Wallet.create()
            creator = AssetCreator(wallet)

            start_time = time.time()
            assets = []

            for i in range(100):
                asset = creator.create_gold_asset(
                    name=f"Rapid Gold {i}",
                    quantity=100.0,
                    unit="troy_oz",
                    purity="99.99%",
                )
                assets.append(asset)

            elapsed = time.time() - start_time

            # All should be unique
            asset_ids = [a["asset_id"] for a in assets]
            assert len(asset_ids) == 100
            assert len(set(asset_ids)) == 100

            print(
                f"    Created 100 assets in {elapsed:.2f}s ({100 / elapsed:.1f} assets/sec)"
            )

            self.log("Rapid asset creation (100 assets)", "PASS")
        except Exception as e:
            self.log("Rapid asset creation", "FAIL", str(e))

    def test_12_asset_ownership_uniqueness(self):
        """Test 12: Verify each asset has correct owner"""
        print("\n[TEST 12] Asset Ownership Uniqueness")
        try:
            # Create 10 different wallets
            wallets = [Wallet.create() for _ in range(10)]

            # Each wallet creates an asset
            assets = []
            for wallet in wallets:
                creator = AssetCreator(wallet)
                asset = creator.create_gold_asset(
                    name=f"Gold for {wallet.address[:10]}",
                    quantity=100.0,
                    unit="troy_oz",
                    purity="99.99%",
                )
                assets.append((wallet.address, asset))

            # Verify ownership
            for wallet_addr, asset in assets:
                assert asset["owner_address"] == wallet_addr

            self.log("Asset ownership uniqueness", "PASS")
        except Exception as e:
            self.log("Asset ownership uniqueness", "FAIL", str(e))

    def test_13_asset_signature_verification(self):
        """Test 13: Verify asset signatures are generated"""
        print("\n[TEST 13] Asset Signature Verification")
        try:
            wallet = Wallet.create()
            creator = AssetCreator(wallet)

            asset = creator.create_gold_asset(
                name="Signed Gold", quantity=100.0, unit="troy_oz", purity="99.99%"
            )

            # Should have signature
            assert "signature" in asset
            assert len(asset["signature"]) > 0

            # Signature should be different for different assets
            asset2 = creator.create_gold_asset(
                name="Signed Gold 2", quantity=100.0, unit="troy_oz", purity="99.99%"
            )

            assert asset["signature"] != asset2["signature"]

            self.log("Asset signature verification", "PASS")
        except Exception as e:
            self.log("Asset signature verification", "FAIL", str(e))

    def test_14_complex_metadata(self):
        """Test 14: Complex nested metadata"""
        print("\n[TEST 14] Complex Metadata")
        try:
            wallet = Wallet.create()
            creator = AssetCreator(wallet)

            complex_metadata = {
                "owner_info": {
                    "name": "John Doe",
                    "company": "Gold Corp",
                    "country": "USA",
                },
                "certifications": ["ISO 9001", "ISO 14001", "LBMA Good Delivery"],
                "insurance": {
                    "provider": "Lloyd's of London",
                    "policy_number": "POL-123456",
                    "coverage": 10000000,
                },
                "audit_trail": [
                    {"date": "2026-01-01", "auditor": "KPMG", "result": "PASS"},
                    {"date": "2026-01-15", "auditor": "Deloitte", "result": "PASS"},
                ],
            }

            asset = creator.create_custom_asset(
                name="Complex Asset",
                description="Asset with complex metadata",
                asset_type=AssetType.GOLD,
                metadata=complex_metadata,
            )

            assert asset["metadata"] == complex_metadata

            self.log("Complex metadata", "PASS")
        except Exception as e:
            self.log("Complex metadata", "FAIL", str(e))

    def test_15_asset_id_collision_resistance(self):
        """Test 15: Asset ID collision resistance"""
        print("\n[TEST 15] Asset ID Collision Resistance")
        try:
            wallet = Wallet.create()
            creator = AssetCreator(wallet)

            # Create identical assets rapidly
            # IDs should still be unique due to timestamp
            assets = []
            for i in range(100):
                asset = creator.create_gold_asset(
                    name="Identical Gold",
                    quantity=100.0,
                    unit="troy_oz",
                    purity="99.99%",
                )
                assets.append(asset["asset_id"])

            # All IDs should be unique
            unique_ids = set(assets)
            assert len(unique_ids) == 100, (
                f"Found {len(unique_ids)} unique IDs out of 100"
            )

            self.log("Asset ID collision resistance", "PASS")
        except Exception as e:
            self.log("Asset ID collision resistance", "FAIL", str(e))

    def run_all_tests(self):
        """Run all stress tests"""
        print("=" * 70)
        print("ASSETS MODULE - MILITARY-GRADE STRESS TESTS")
        print("=" * 70)

        self.test_1_basic_asset_creator()
        self.test_2_gold_asset_all_units()
        self.test_3_land_asset_all_units()
        self.test_4_fractional_assets()
        self.test_5_asset_with_all_metadata()
        self.test_6_custom_asset_types()
        self.test_7_extreme_values()
        self.test_8_special_characters_in_names()
        self.test_9_empty_optional_fields()
        self.test_10_concurrent_asset_creation()
        self.test_11_rapid_asset_creation()
        self.test_12_asset_ownership_uniqueness()
        self.test_13_asset_signature_verification()
        self.test_14_complex_metadata()
        self.test_15_asset_id_collision_resistance()

        print("\n" + "=" * 70)
        print("ASSETS STRESS TEST RESULTS")
        print("=" * 70)
        print(f"Total Tests: {self.passed + self.failed}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Success Rate: {(self.passed / (self.passed + self.failed) * 100):.1f}%")
        print("=" * 70)

        if self.failed > 0:
            print("\nFailed Tests:")
            for result in self.results:
                if result["status"] == "FAIL":
                    print(f"  - {result['test']}: {result['message']}")

        return self.failed == 0


if __name__ == "__main__":
    tester = AssetsStressTest()
    success = tester.run_all_tests()

    if success:
        print("\n[OK] All assets stress tests passed!")
        sys.exit(0)
    else:
        print("\n[WARNING] Some tests failed - review above")
        sys.exit(1)
