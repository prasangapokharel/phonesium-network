"""
Phonesium Wallet - Secure wallet management with encryption
"""
import hashlib
import orjson
import base64
import os
from pathlib import Path
from typing import Optional
from ecdsa import SigningKey, VerifyingKey, SECP256k1
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from .exceptions import WalletError, InvalidAddressError


class Wallet:
    """
    PHN Blockchain Wallet with Encryption Support
    
    Full-featured wallet with encryption, signing, and key management.
    
    Example:
        # Create new wallet
        wallet = Wallet.create()
        print(f"Address: {wallet.address}")
        
        # Get private key (with warning)
        private_key = wallet.get_private_key(show_warning=True)
        
        # Save wallet with encryption
        wallet.save("my_wallet.json", password="secure_password_123")
        
        # Load encrypted wallet
        wallet = Wallet.load("my_wallet.json", password="secure_password_123")
    """
    
    def __init__(self, private_key: str, public_key: str, address: str):
        """Initialize wallet with keys"""
        self._private_key = private_key  # Private - use get_private_key()
        self.public_key = public_key
        self.address = address
        self._signing_key = SigningKey.from_string(bytes.fromhex(private_key), curve=SECP256k1)
    
    @property
    def private_key(self) -> str:
        """
        Get private key with warning
        DEPRECATED: Use get_private_key() instead
        """
        print("[SECURITY WARNING] Accessing private key directly!")
        print("[SECURITY WARNING] Use wallet.get_private_key(show_warning=True) instead")
        return self._private_key
    
    def get_private_key(self, show_warning: bool = True) -> str:
        """
        Get private key with optional security warning
        
        Args:
            show_warning: Show security warning (recommended)
            
        Returns:
            str: Private key (64 hex characters)
            
        Warning:
            NEVER share your private key with anyone!
            Anyone with your private key can steal ALL your funds!
        """
        if show_warning:
            print("\n" + "="*60)
            print("SECURITY WARNING - PRIVATE KEY ACCESS")
            print("="*60)
            print("You are accessing your private key.")
            print("NEVER share this with anyone!")
            print("Anyone with this key can steal ALL your funds!")
            print("="*60 + "\n")
        
        return self._private_key
    
    @classmethod
    def create(cls) -> 'Wallet':
        """
        Create a new wallet with random keys
        
        Returns:
            Wallet: New wallet instance
        """
        # Generate private key
        sk = SigningKey.generate(curve=SECP256k1)
        private_key = sk.to_string().hex()
        
        # Get public key
        vk = sk.get_verifying_key()
        public_key = vk.to_string().hex()
        
        # Generate PHN address
        address = cls._generate_address(public_key)
        
        return cls(private_key, public_key, address)
    
    @classmethod
    def from_private_key(cls, private_key: str) -> 'Wallet':
        """
        Create wallet from existing private key
        
        Args:
            private_key: 64-character hex private key
            
        Returns:
            Wallet: Wallet instance
            
        Raises:
            WalletError: If private key is invalid
        """
        try:
            # Validate format
            if len(private_key) != 64:
                raise ValueError("Private key must be 64 hex characters")
            
            sk = SigningKey.from_string(bytes.fromhex(private_key), curve=SECP256k1)
            vk = sk.get_verifying_key()
            public_key = vk.to_string().hex()
            address = cls._generate_address(public_key)
            return cls(private_key, public_key, address)
        except Exception as e:
            raise WalletError(f"Invalid private key: {e}")
    
    @staticmethod
    def _generate_address(public_key: str) -> str:
        """Generate PHN address from public key"""
        public_key_bytes = bytes.fromhex(public_key)
        address_hash = hashlib.sha256(public_key_bytes).hexdigest()[:40]
        return f"PHN{address_hash}"
    
    @staticmethod
    def _derive_key(password: str, salt: bytes) -> bytes:
        """Derive encryption key from password"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))
    
    def save(self, filepath: str, password: Optional[str] = None) -> None:
        """
        Save wallet to file with optional encryption
        
        Args:
            filepath: Path to save wallet
            password: Password for encryption (STRONGLY RECOMMENDED!)
            
        Note:
            Without password, private key is stored in PLAIN TEXT!
            This is VERY DANGEROUS - anyone with file access can steal your funds!
        """
        wallet_data = {
            "address": self.address,
            "public_key": self.public_key,
            "private_key": self._private_key
        }
        
        if password:
            # Encrypt wallet with password
            salt = os.urandom(16)
            key = self._derive_key(password, salt)
            f = Fernet(key)
            
            # Encrypt the private key
            encrypted_private_key = f.encrypt(self._private_key.encode()).decode()
            
            wallet_data = {
                "address": self.address,
                "public_key": self.public_key,
                "private_key": encrypted_private_key,
                "encrypted": True,
                "salt": base64.b64encode(salt).decode()
            }
            print(f"[SECURITY] Wallet encrypted with password")
        else:
            print("\n" + "="*60)
            print("WARNING: Saving wallet WITHOUT encryption!")
            print("="*60)
            print("Private key will be stored in PLAIN TEXT!")
            print("This is DANGEROUS - anyone with file access can steal funds!")
            print("Use password parameter for encryption!")
            print("="*60 + "\n")
            wallet_data["encrypted"] = False
        
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            f.write(orjson.dumps(wallet_data, option=orjson.OPT_INDENT_2))
        
        print(f"[INFO] Wallet saved to: {filepath}")
    
    @classmethod
    def load(cls, filepath: str, password: Optional[str] = None) -> 'Wallet':
        """
        Load wallet from file
        
        Args:
            filepath: Path to wallet file
            password: Password if wallet is encrypted
            
        Returns:
            Wallet: Loaded wallet instance
            
        Raises:
            WalletError: If file not found, invalid format, or wrong password
        """
        try:
            with open(filepath, 'r') as f:
                wallet_data = orjson.loads(f.read())
            
            # Check if encrypted
            if wallet_data.get("encrypted", False):
                if not password:
                    raise WalletError("Wallet is encrypted but no password provided")
                
                # Decrypt private key
                salt = base64.b64decode(wallet_data["salt"])
                key = cls._derive_key(password, salt)
                f = Fernet(key)
                
                try:
                    private_key = f.decrypt(wallet_data["private_key"].encode()).decode()
                except Exception:
                    raise WalletError("Invalid password")
            else:
                private_key = wallet_data["private_key"]
                print("[WARNING] Wallet is NOT encrypted - private key in plaintext")
            
            return cls(
                private_key,
                wallet_data["public_key"],
                wallet_data["address"]
            )
        except FileNotFoundError:
            raise WalletError(f"Wallet file not found: {filepath}")
        except WalletError:
            raise
        except Exception as e:
            raise WalletError(f"Failed to load wallet: {e}")
    
    def sign(self, data) -> str:
        """
        Sign data with private key
        
        Args:
            data: Data to sign (string or bytes)
            
        Returns:
            str: Hex-encoded signature
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        return self._signing_key.sign(data).hex()
    
    def verify_signature(self, data, signature: str) -> bool:
        """
        Verify a signature
        
        Args:
            data: Original data (string or bytes)
            signature: Hex-encoded signature
            
        Returns:
            bool: True if signature is valid
        """
        try:
            if isinstance(data, str):
                data = data.encode('utf-8')
            vk = VerifyingKey.from_string(bytes.fromhex(self.public_key), curve=SECP256k1)
            return vk.verify(bytes.fromhex(signature), data)
        except:
            return False
    
    def to_dict(self, include_private_key: bool = False) -> dict:
        """
        Convert wallet to dictionary
        
        Args:
            include_private_key: Include private key (DANGEROUS!)
            
        Returns:
            dict: Wallet data
        """
        data = {
            "address": self.address,
            "public_key": self.public_key,
        }
        
        if include_private_key:
            print("[WARNING] Including private key in export - keep this data safe!")
            data["private_key"] = self._private_key
        
        return data
    
    def export_private_key(self, confirm: bool = False) -> str:
        """
        Export private key with confirmation
        
        Args:
            confirm: Must be True to export
            
        Returns:
            str: Private key
            
        Raises:
            WalletError: If not confirmed
        """
        if not confirm:
            raise WalletError(
                "You must confirm private key export by setting confirm=True. "
                "Remember: NEVER share your private key!"
            )
        
        return self.get_private_key(show_warning=True)
    
    def export_wallet(self, include_private_key: bool = False) -> dict:
        """
        Export wallet data as dictionary
        
        Args:
            include_private_key: Include private key in export (DANGEROUS!)
            
        Returns:
            dict: Wallet data
        """
        return self.to_dict(include_private_key=include_private_key)
    
    def create_transaction(self, recipient: str, amount: float, fee: float = 1.0) -> dict:
        """
        Create and sign a transaction
        
        Args:
            recipient: Recipient PHN address
            amount: Amount to send
            fee: Transaction fee (default 1.0)
            
        Returns:
            dict: Signed transaction ready to broadcast
        """
        import time
        import secrets
        import hashlib
        
        # Generate nonce
        nonce = secrets.token_hex(16)
        timestamp = int(time.time())
        
        # Create transaction data
        tx_data = f"{self.address}{recipient}{amount}{fee}{timestamp}{nonce}"
        
        # Calculate TXID
        txid = hashlib.sha256(tx_data.encode()).hexdigest()
        
        # Sign transaction
        signature = self.sign(tx_data)
        
        return {
            "sender": self.address,
            "recipient": recipient,
            "amount": amount,
            "fee": fee,
            "timestamp": timestamp,
            "nonce": nonce,
            "txid": txid,
            "signature": signature
        }
    
    def __repr__(self) -> str:
        return f"Wallet(address={self.address})"
    
    def __str__(self) -> str:
        return f"PHN Wallet\nAddress: {self.address}\nPublic Key: {self.public_key[:20]}..."

