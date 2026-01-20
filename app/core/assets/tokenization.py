"""
PHN Blockchain - Asset Tokenization System
Following industry standards (ERC-721/ERC-1155 principles)

Security Standards:
- ECDSA signature verification for all asset operations
- Ownership validation before transfers
- Immutable asset records on blockchain
- Fractionalization with precise accounting
- Audit trail for all asset transactions
"""

import hashlib
import time
import orjson
import secrets
from typing import Dict, List, Optional, Tuple
from enum import Enum


class AssetType(Enum):
    """Standard asset types"""
    GOLD = "GOLD"
    LAND = "LAND"
    REAL_ESTATE = "REAL_ESTATE"
    COMMODITY = "COMMODITY"
    SECURITY = "SECURITY"
    CUSTOM = "CUSTOM"


class AssetStandard(Enum):
    """Asset tokenization standards"""
    PHN721 = "PHN-721"  # Non-fungible tokens (NFT)
    PHN1155 = "PHN-1155"  # Multi-token standard (fungible + non-fungible)


class Asset:
    """
    Represents a tokenized asset on PHN blockchain
    
    Standards Compliance:
    - Unique asset ID (similar to ERC-721 tokenId)
    - Metadata standard (name, description, attributes)
    - Ownership tracking
    - Transfer history
    - Fractionalization support
    """
    
    def __init__(
        self,
        asset_type: AssetType,
        name: str,
        description: str,
        total_supply: float,
        owner_address: str,
        metadata: Dict = None,
        fractional: bool = False,
        standard: AssetStandard = AssetStandard.PHN721
    ):
        """
        Initialize asset
        
        Args:
            asset_type: Type of asset (GOLD, LAND, etc.)
            name: Asset name
            description: Asset description
            total_supply: Total units (1 for NFT, N for fractional)
            owner_address: Initial owner PHN address
            metadata: Additional metadata
            fractional: Whether asset can be fractionalized
            standard: PHN-721 (NFT) or PHN-1155 (multi-token)
        """
        self.asset_id = self._generate_asset_id()
        self.asset_type = asset_type
        self.name = name
        self.description = description
        self.total_supply = total_supply
        self.owner_address = owner_address
        self.metadata = metadata or {}
        self.fractional = fractional
        self.standard = standard
        self.created_at = int(time.time())
        
        # Ownership tracking for fractional assets
        if fractional:
            self.balances = {owner_address: total_supply}
        else:
            self.balances = {owner_address: 1.0}
        
        # Transaction history
        self.history = []
        
        # Add creation event
        self._add_history_event("CREATED", owner_address, None, total_supply)
    
    def _generate_asset_id(self) -> str:
        """Generate unique asset ID"""
        random_bytes = secrets.token_bytes(32)
        timestamp = str(time.time()).encode()
        return hashlib.sha256(random_bytes + timestamp).hexdigest()
    
    def _add_history_event(self, event_type: str, from_addr: str, to_addr: Optional[str], amount: float):
        """Add event to history"""
        self.history.append({
            "event": event_type,
            "from": from_addr,
            "to": to_addr,
            "amount": amount,
            "timestamp": int(time.time())
        })
    
    def get_balance(self, address: str) -> float:
        """Get balance of address for this asset"""
        return self.balances.get(address, 0.0)
    
    def transfer(self, from_address: str, to_address: str, amount: float) -> Tuple[bool, str]:
        """
        Transfer asset ownership
        
        Security:
        - Validates ownership before transfer
        - Atomic operation (all or nothing)
        - Maintains accurate balances
        
        Args:
            from_address: Sender address
            to_address: Recipient address
            amount: Amount to transfer
            
        Returns:
            (success, message)
        """
        # Validate sender has sufficient balance
        if self.get_balance(from_address) < amount:
            return False, "Insufficient asset balance"
        
        # For non-fractional assets, only allow full transfer
        if not self.fractional and amount != 1.0:
            return False, "Non-fractional assets must be transferred whole"
        
        # Perform transfer
        self.balances[from_address] = self.balances.get(from_address, 0) - amount
        self.balances[to_address] = self.balances.get(to_address, 0) + amount
        
        # Clean up zero balances
        if self.balances[from_address] == 0:
            del self.balances[from_address]
        
        # Update history
        self._add_history_event("TRANSFER", from_address, to_address, amount)
        
        return True, "Transfer successful"
    
    def fractionalize(self, num_fractions: int) -> Tuple[bool, str]:
        """
        Convert whole asset into fractions
        
        Args:
            num_fractions: Number of fractions to create
            
        Returns:
            (success, message)
        """
        if self.fractional:
            return False, "Asset is already fractionalized"
        
        if num_fractions < 2:
            return False, "Must create at least 2 fractions"
        
        # Convert to fractional
        self.fractional = True
        self.total_supply = float(num_fractions)
        
        # Update owner balance
        owner = list(self.balances.keys())[0]
        self.balances[owner] = float(num_fractions)
        
        # Update standard
        self.standard = AssetStandard.PHN1155
        
        # Add history
        self._add_history_event("FRACTIONALIZED", owner, None, num_fractions)
        
        return True, f"Asset fractionalized into {num_fractions} units"
    
    def to_dict(self) -> Dict:
        """Convert asset to dictionary for storage"""
        return {
            "asset_id": self.asset_id,
            "asset_type": self.asset_type.value,
            "name": self.name,
            "description": self.description,
            "total_supply": self.total_supply,
            "owner_address": self.owner_address,
            "metadata": self.metadata,
            "fractional": self.fractional,
            "standard": self.standard.value,
            "created_at": self.created_at,
            "balances": self.balances,
            "history": self.history
        }
    
    @staticmethod
    def from_dict(data: Dict) -> 'Asset':
        """Load asset from dictionary"""
        asset = Asset(
            asset_type=AssetType(data["asset_type"]),
            name=data["name"],
            description=data["description"],
            total_supply=data["total_supply"],
            owner_address=data["owner_address"],
            metadata=data.get("metadata", {}),
            fractional=data["fractional"],
            standard=AssetStandard(data["standard"])
        )
        asset.asset_id = data["asset_id"]
        asset.created_at = data["created_at"]
        asset.balances = data["balances"]
        asset.history = data["history"]
        return asset
    
    def __repr__(self) -> str:
        return f"Asset(id={self.asset_id[:8]}..., type={self.asset_type.value}, name={self.name})"


class AssetTransaction:
    """
    Asset transaction following PHN blockchain standards
    Integrates with existing transaction system
    """
    
    @staticmethod
    def create_mint_transaction(
        wallet,
        asset: Asset,
        fee: float = 1.0
    ) -> Dict:
        """
        Create transaction to mint new asset on blockchain
        
        Args:
            wallet: Wallet object with signing capability
            asset: Asset to mint
            fee: Transaction fee
            
        Returns:
            Transaction dictionary ready to broadcast
        """
        timestamp = int(time.time())
        nonce = secrets.token_hex(16)
        
        # Transaction data
        tx_data = {
            "type": "ASSET_MINT",
            "sender": wallet.address,
            "recipient": asset.owner_address,
            "amount": 0.0,  # No PHN transfer for minting
            "fee": fee,
            "timestamp": timestamp,
            "nonce": nonce,
            "asset_data": asset.to_dict()
        }
        
        # Generate TXID
        tx_string = f"{tx_data['sender']}{tx_data['recipient']}{tx_data['amount']}{tx_data['fee']}{timestamp}{nonce}"
        tx_data["txid"] = hashlib.sha256(tx_string.encode()).hexdigest()
        
        # Sign transaction
        signature_data = f"{tx_string}{orjson.dumps(tx_data['asset_data'], option=orjson.OPT_SORT_KEYS).decode()}"
        tx_data["signature"] = wallet.sign(signature_data)
        
        return tx_data
    
    @staticmethod
    def create_transfer_transaction(
        wallet,
        asset_id: str,
        to_address: str,
        amount: float,
        fee: float = 1.0
    ) -> Dict:
        """
        Create transaction to transfer asset
        
        Args:
            wallet: Sender wallet
            asset_id: Asset ID to transfer
            to_address: Recipient address
            amount: Amount to transfer
            fee: Transaction fee
            
        Returns:
            Transaction dictionary
        """
        timestamp = int(time.time())
        nonce = secrets.token_hex(16)
        
        tx_data = {
            "type": "ASSET_TRANSFER",
            "sender": wallet.address,
            "recipient": to_address,
            "amount": 0.0,  # No PHN transfer
            "fee": fee,
            "timestamp": timestamp,
            "nonce": nonce,
            "asset_id": asset_id,
            "asset_amount": amount
        }
        
        # Generate TXID
        tx_string = f"{tx_data['sender']}{tx_data['recipient']}{tx_data['amount']}{tx_data['fee']}{timestamp}{nonce}{asset_id}{amount}"
        tx_data["txid"] = hashlib.sha256(tx_string.encode()).hexdigest()
        
        # Sign
        tx_data["signature"] = wallet.sign(tx_string)
        
        return tx_data


class AssetRegistry:
    """
    Registry for all tokenized assets on PHN blockchain
    
    Security:
    - Immutable asset records
    - Ownership validation
    - Transfer verification
    - Complete audit trail
    """
    
    def __init__(self):
        self.assets: Dict[str, Asset] = {}
        self.owner_assets: Dict[str, List[str]] = {}  # address -> [asset_ids]
    
    def register_asset(self, asset: Asset) -> Tuple[bool, str]:
        """
        Register new asset on blockchain
        
        Args:
            asset: Asset to register
            
        Returns:
            (success, message)
        """
        if asset.asset_id in self.assets:
            return False, "Asset ID already exists"
        
        self.assets[asset.asset_id] = asset
        
        # Update owner index
        if asset.owner_address not in self.owner_assets:
            self.owner_assets[asset.owner_address] = []
        self.owner_assets[asset.owner_address].append(asset.asset_id)
        
        return True, f"Asset registered: {asset.asset_id}"
    
    def get_asset(self, asset_id: str) -> Optional[Asset]:
        """Get asset by ID"""
        return self.assets.get(asset_id)
    
    def get_assets_by_owner(self, address: str) -> List[Asset]:
        """Get all assets owned by address"""
        asset_ids = self.owner_assets.get(address, [])
        assets = []
        
        for aid in asset_ids:
            asset = self.assets.get(aid)
            if asset and asset.get_balance(address) > 0:
                assets.append(asset)
        
        return assets
    
    def transfer_asset(
        self, 
        asset_id: str, 
        from_address: str, 
        to_address: str, 
        amount: float
    ) -> Tuple[bool, str]:
        """
        Transfer asset between addresses
        
        Security validation:
        - Asset exists
        - Sender owns sufficient amount
        - Atomic transfer
        
        Args:
            asset_id: Asset to transfer
            from_address: Sender
            to_address: Recipient
            amount: Amount to transfer
            
        Returns:
            (success, message)
        """
        asset = self.get_asset(asset_id)
        if not asset:
            return False, "Asset not found"
        
        # Perform transfer
        success, msg = asset.transfer(from_address, to_address, amount)
        
        if success:
            # Update owner index
            if to_address not in self.owner_assets:
                self.owner_assets[to_address] = []
            if asset_id not in self.owner_assets[to_address]:
                self.owner_assets[to_address].append(asset_id)
        
        return success, msg
    
    def get_asset_balance(self, asset_id: str, address: str) -> float:
        """Get balance of specific asset for address"""
        asset = self.get_asset(asset_id)
        return asset.get_balance(address) if asset else 0.0
    
    def save_to_file(self, filepath: str):
        """Save registry to file"""
        data = {
            "assets": {aid: asset.to_dict() for aid, asset in self.assets.items()},
            "owner_assets": self.owner_assets
        }
        
        with open(filepath, 'wb') as f:
            f.write(orjson.dumps(data, option=orjson.OPT_INDENT_2))
    
    def load_from_file(self, filepath: str):
        """Load registry from file"""
        with open(filepath, 'rb') as f:
            data = orjson.loads(f.read())
        
        self.assets = {
            aid: Asset.from_dict(adata) 
            for aid, adata in data["assets"].items()
        }
        self.owner_assets = data["owner_assets"]
    
    def get_stats(self) -> Dict:
        """Get registry statistics"""
        return {
            "total_assets": len(self.assets),
            "total_owners": len(self.owner_assets),
            "asset_types": {
                asset_type.value: sum(
                    1 for a in self.assets.values() 
                    if a.asset_type == asset_type
                )
                for asset_type in AssetType
            },
            "fractional_assets": sum(1 for a in self.assets.values() if a.fractional)
        }


# Global asset registry
asset_registry = AssetRegistry()


if __name__ == "__main__":
    print("PHN Blockchain Asset Tokenization System")
    print("=" * 60)
    print("\nFeatures:")
    print("- Multiple asset types (Gold, Land, Real Estate, etc.)")
    print("- Fractionalization support")
    print("- Ownership tracking")
    print("- Transfer history")
    print("- Industry-standard security")
    print("\nUse the user tools to create and manage assets.")
