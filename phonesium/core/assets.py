"""
Phonesium Assets Module - Asset Creation and Management
Simple API for creating tokenized assets on PHN blockchain
"""

import hashlib
import time
import requests
from typing import Dict, Optional
from enum import Enum

from .config import DEFAULT_NODE_URL
from .wallet import Wallet
from .exceptions import NetworkError, InvalidTransactionError


class AssetType(Enum):
    """Asset types supported by PHN blockchain"""

    GOLD = "gold"
    LAND = "land"
    REAL_ESTATE = "real_estate"
    COMMODITY = "commodity"
    SECURITY = "security"
    CUSTOM = "custom"


class AssetCreator:
    """
    Create and manage tokenized assets

    Example:
        >>> from phonesium import Wallet, AssetCreator
        >>>
        >>> wallet = Wallet.create()
        >>> creator = AssetCreator(wallet)
        >>>
        >>> # Create gold asset
        >>> asset = creator.create_gold_asset(
        ...     name="Premium Gold Bar",
        ...     quantity=100.0,
        ...     unit="troy_oz",
        ...     purity="99.99%"
        ... )
        >>>
        >>> # Create land asset
        >>> asset = creator.create_land_asset(
        ...     name="Prime Land Plot",
        ...     area=50.0,
        ...     unit="acres",
        ...     location="California, USA"
        ... )
    """

    def __init__(self, wallet: Wallet, node_url: str = None):
        """
        Initialize asset creator

        Args:
            wallet: Owner wallet
            node_url: PHN node URL (default from config)
        """
        self.wallet = wallet
        self.node_url = (node_url or DEFAULT_NODE_URL).rstrip("/")

    def create_gold_asset(
        self,
        name: str,
        quantity: float,
        unit: str = "troy_oz",
        purity: str = "99.99%",
        serial_number: str = "",
        certificate: str = "",
        vault_location: str = "",
        fractional: bool = False,
        total_supply: float = 1.0,
    ) -> Dict:
        """
        Create tokenized gold asset

        Args:
            name: Asset name
            quantity: Amount of gold
            unit: Unit (troy_oz, g, kg)
            purity: Gold purity
            serial_number: Serial number (optional)
            certificate: Certificate ID (optional)
            vault_location: Storage location (optional)
            fractional: Allow fractional ownership
            total_supply: Number of fractions if fractional

        Returns:
            dict: Created asset data
        """
        metadata = {
            "unit": unit,
            "quantity": quantity,
            "purity": purity,
            "serial_number": serial_number,
            "certificate": certificate,
            "vault_location": vault_location,
            "verification_date": None,
            "insured": False,
        }

        description = f"{quantity} {unit} of Gold, Purity: {purity}"
        if serial_number:
            description += f", Serial: {serial_number}"

        return self._create_asset(
            asset_type=AssetType.GOLD,
            name=name,
            description=description,
            metadata=metadata,
            fractional=fractional,
            total_supply=total_supply,
        )

    def create_land_asset(
        self,
        name: str,
        area: float,
        unit: str = "acres",
        location: str = "",
        land_use: str = "",
        deed_number: str = "",
        parcel_id: str = "",
        zoning: str = "",
        fractional: bool = False,
        total_supply: float = 1.0,
    ) -> Dict:
        """
        Create tokenized land asset

        Args:
            name: Asset name
            area: Land area
            unit: Unit (acres, hectares, sqft, sqm)
            location: Location address/coordinates
            land_use: Land use type
            deed_number: Deed/title number
            parcel_id: Parcel ID (optional)
            zoning: Zoning classification
            fractional: Allow fractional ownership
            total_supply: Number of fractions if fractional

        Returns:
            dict: Created asset data
        """
        metadata = {
            "unit": unit,
            "area": area,
            "location": location,
            "land_use": land_use,
            "deed_number": deed_number,
            "parcel_id": parcel_id,
            "zoning": zoning,
            "surveyed": False,
            "encumbrances": [],
        }

        description = f"{area} {unit} of Land, Location: {location}"
        if land_use:
            description += f", Use: {land_use}"

        return self._create_asset(
            asset_type=AssetType.LAND,
            name=name,
            description=description,
            metadata=metadata,
            fractional=fractional,
            total_supply=total_supply,
        )

    def create_custom_asset(
        self,
        name: str,
        description: str,
        asset_type: AssetType = AssetType.CUSTOM,
        metadata: Dict = None,
        fractional: bool = False,
        total_supply: float = 1.0,
    ) -> Dict:
        """
        Create custom tokenized asset

        Args:
            name: Asset name
            description: Asset description
            asset_type: Type of asset
            metadata: Custom metadata dictionary
            fractional: Allow fractional ownership
            total_supply: Number of fractions if fractional

        Returns:
            dict: Created asset data
        """
        return self._create_asset(
            asset_type=asset_type,
            name=name,
            description=description,
            metadata=metadata or {},
            fractional=fractional,
            total_supply=total_supply,
        )

    def _create_asset(
        self,
        asset_type: AssetType,
        name: str,
        description: str,
        metadata: Dict,
        fractional: bool,
        total_supply: float,
    ) -> Dict:
        """Internal method to create asset"""
        timestamp = time.time()

        # Generate asset ID
        asset_data = f"{self.wallet.address}{name}{description}{timestamp}"
        asset_id = hashlib.sha256(asset_data.encode()).hexdigest()

        asset = {
            "asset_id": asset_id,
            "asset_type": asset_type.value,
            "name": name,
            "description": description,
            "owner_address": self.wallet.address,
            "total_supply": total_supply,
            "fractional": fractional,
            "metadata": metadata,
            "created_at": timestamp,
            "signature": "",
        }

        # Sign asset
        asset["signature"] = self.wallet.sign(str(asset))

        # Submit to blockchain (if node API supports it)
        try:
            response = requests.post(
                f"{self.node_url}/create_asset", json={"asset": asset}, timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                print(f"[Assets] Asset created successfully: {asset_id[:16]}...")
                return result.get("asset", asset)
            else:
                print(f"[Assets] Warning: Node returned {response.status_code}")
                print(f"[Assets] Asset created locally: {asset_id[:16]}...")
                return asset

        except requests.RequestException as e:
            print(f"[Assets] Warning: Could not submit to node: {e}")
            print(f"[Assets] Asset created locally: {asset_id[:16]}...")
            return asset

    def get_asset(self, asset_id: str) -> Optional[Dict]:
        """
        Get asset by ID

        Args:
            asset_id: Asset ID

        Returns:
            dict: Asset data or None if not found
        """
        try:
            response = requests.get(f"{self.node_url}/asset/{asset_id}", timeout=10)

            if response.status_code == 200:
                return response.json()
            else:
                return None

        except requests.RequestException as e:
            raise NetworkError(f"Failed to get asset: {e}")

    def list_assets(self, owner_address: Optional[str] = None) -> list:
        """
        List all assets, optionally filtered by owner

        Args:
            owner_address: Filter by owner address (optional)

        Returns:
            list: List of assets
        """
        try:
            params = {"owner": owner_address} if owner_address else {}
            response = requests.get(
                f"{self.node_url}/assets", params=params, timeout=10
            )

            if response.status_code == 200:
                return response.json().get("assets", [])
            else:
                return []

        except requests.RequestException as e:
            raise NetworkError(f"Failed to list assets: {e}")


def create_asset(
    wallet: Wallet,
    asset_type: str,
    name: str,
    description: str = "",
    metadata: Dict = None,
    fractional: bool = False,
    total_supply: float = 1.0,
    node_url: str = "http://localhost:8765",
) -> Dict:
    """
    Convenience function to create an asset

    Args:
        wallet: Owner wallet
        asset_type: Asset type (gold, land, custom, etc.)
        name: Asset name
        description: Asset description
        metadata: Custom metadata
        fractional: Allow fractional ownership
        total_supply: Number of fractions
        node_url: PHN node URL

    Returns:
        dict: Created asset
    """
    creator = AssetCreator(wallet, node_url)

    try:
        asset_type_enum = AssetType(asset_type.lower())
    except ValueError:
        asset_type_enum = AssetType.CUSTOM

    return creator.create_custom_asset(
        name=name,
        description=description,
        asset_type=asset_type_enum,
        metadata=metadata or {},
        fractional=fractional,
        total_supply=total_supply,
    )
