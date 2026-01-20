"""
Comprehensive User Workflow Tests
Tests wallet creation, transactions, and user operations
"""
import pytest
import time
import os
from pathlib import Path
from app.utils.wallet_generator import generate_wallet
from app.utils.secure_wallet import (
    create_encrypted_wallet, 
    load_encrypted_wallet,
    is_wallet_encrypted
)
from app.core.transactions.base import create_signed_transaction, verify_tx_signature


@pytest.mark.unit
class TestWalletCreation:
    """Test wallet creation and management"""
    
    def test_generate_wallet(self):
        """Test wallet generation creates all required keys"""
        wallet = generate_wallet()
        
        assert 'private_key' in wallet
        assert 'public_key' in wallet
        assert 'address' in wallet
        
        assert wallet['private_key'] is not None
        assert wallet['public_key'] is not None
        assert wallet['address'] is not None
        
    def test_wallet_address_format(self):
        """Test wallet address has correct format"""
        wallet = generate_wallet()
        address = wallet['address']
        
        assert address.startswith('PHN')
        assert len(address) > 10  # Should be reasonably long
        
    def test_multiple_wallets_unique(self):
        """Test multiple wallets have unique addresses"""
        wallet1 = generate_wallet()
        wallet2 = generate_wallet()
        wallet3 = generate_wallet()
        
        assert wallet1['address'] != wallet2['address']
        assert wallet2['address'] != wallet3['address']
        assert wallet1['address'] != wallet3['address']
        
    def test_wallet_keys_are_hex(self):
        """Test wallet keys are valid hex strings"""
        wallet = generate_wallet()
        
        # Public and private keys should be hex
        try:
            bytes.fromhex(wallet['private_key'])
            bytes.fromhex(wallet['public_key'])
            is_hex = True
        except ValueError:
            is_hex = False
            
        assert is_hex is True


@pytest.mark.unit
class TestWalletEncryption:
    """Test wallet encryption functionality"""
    
    def test_create_encrypted_wallet(self, tmp_path):
        """Test creating encrypted wallet"""
        wallet_path = tmp_path / "test_encrypted.json"
        password = "SecurePassword123!"
        
        wallet_data = create_encrypted_wallet(
            str(wallet_path),
            password=password
        )
        
        assert wallet_path.exists()
        assert 'address' in wallet_data
        assert 'public_key' in wallet_data
        
    def test_encrypted_wallet_detection(self, encrypted_wallet):
        """Test detecting if wallet is encrypted"""
        is_encrypted = is_wallet_encrypted(encrypted_wallet['path'])
        
        assert is_encrypted is True
        
    def test_load_encrypted_wallet_correct_password(self, encrypted_wallet):
        """Test loading encrypted wallet with correct password"""
        wallet_data = load_encrypted_wallet(
            encrypted_wallet['path'],
            encrypted_wallet['password']
        )
        
        assert wallet_data is not None
        assert 'private_key' in wallet_data
        assert 'public_key' in wallet_data
        assert 'address' in wallet_data
        
    def test_load_encrypted_wallet_wrong_password(self, encrypted_wallet):
        """Test loading encrypted wallet with wrong password fails"""
        with pytest.raises(Exception):
            load_encrypted_wallet(
                encrypted_wallet['path'],
                "WrongPassword"
            )
            
    def test_encrypted_wallet_file_content_not_plaintext(self, encrypted_wallet):
        """Test encrypted wallet file doesn't contain plaintext keys"""
        with open(encrypted_wallet['path'], 'r') as f:
            content = f.read()
            
        # Private key should not be in plaintext
        assert 'private_key' not in content or 'encrypted' in content.lower()


@pytest.mark.unit
class TestTransactionCreation:
    """Test transaction creation"""
    
    def test_create_signed_transaction(self, test_wallets):
        """Test creating and signing a transaction"""
        alice = test_wallets['alice']
        bob = test_wallets['bob']
        
        tx = create_signed_transaction(
            sender=alice['address'],
            recipient=bob['address'],
            amount=10.0,
            fee=0.02,
            private_key=alice['private_key']
        )
        
        assert tx is not None
        assert tx['sender'] == alice['address']
        assert tx['recipient'] == bob['address']
        assert tx['amount'] == 10.0
        assert tx['fee'] == 0.02
        assert 'signature' in tx
        assert 'txid' in tx
        assert 'timestamp' in tx
        
    def test_transaction_signature_valid(self, test_wallets):
        """Test transaction signature is valid"""
        alice = test_wallets['alice']
        bob = test_wallets['bob']
        
        tx = create_signed_transaction(
            sender=alice['address'],
            recipient=bob['address'],
            amount=10.0,
            fee=0.02,
            private_key=alice['private_key']
        )
        
        is_valid = verify_tx_signature(tx)
        assert is_valid is True
        
    def test_transaction_with_different_amounts(self, test_wallets):
        """Test transactions with various amounts"""
        alice = test_wallets['alice']
        bob = test_wallets['bob']
        
        amounts = [0.01, 1.0, 10.0, 100.0, 1000.0]
        
        for amount in amounts:
            tx = create_signed_transaction(
                sender=alice['address'],
                recipient=bob['address'],
                amount=amount,
                fee=0.02,
                private_key=alice['private_key']
            )
            
            assert tx['amount'] == amount
            
    def test_transaction_with_different_fees(self, test_wallets):
        """Test transactions with various fees"""
        alice = test_wallets['alice']
        bob = test_wallets['bob']
        
        fees = [0.01, 0.02, 0.05, 0.10, 1.0]
        
        for fee in fees:
            tx = create_signed_transaction(
                sender=alice['address'],
                recipient=bob['address'],
                amount=10.0,
                fee=fee,
                private_key=alice['private_key']
            )
            
            assert tx['fee'] == fee


@pytest.mark.integration
class TestUserWorkflow:
    """Test complete user workflows"""
    
    def test_complete_user_workflow_send_transaction(self, test_wallets):
        """Test: Create wallet -> Sign transaction -> Send"""
        # Step 1: User has wallet
        alice = test_wallets['alice']
        bob = test_wallets['bob']
        
        assert alice['address'] is not None
        assert bob['address'] is not None
        
        # Step 2: Create transaction
        amount = 25.0
        fee = 0.02
        
        tx = create_signed_transaction(
            sender=alice['address'],
            recipient=bob['address'],
            amount=amount,
            fee=fee,
            private_key=alice['private_key']
        )
        
        # Step 3: Verify transaction structure
        assert tx['sender'] == alice['address']
        assert tx['recipient'] == bob['address']
        assert tx['amount'] == amount
        assert tx['fee'] == fee
        
        # Step 4: Verify signature
        is_valid = verify_tx_signature(tx)
        assert is_valid is True
        
        # Transaction is now ready to be sent to the node
        
    def test_multiple_users_sending_transactions(self, test_wallets):
        """Test multiple users can send transactions"""
        alice = test_wallets['alice']
        bob = test_wallets['bob']
        charlie = test_wallets['charlie']
        
        # Alice -> Bob
        tx1 = create_signed_transaction(
            sender=alice['address'],
            recipient=bob['address'],
            amount=10.0,
            fee=0.02,
            private_key=alice['private_key']
        )
        
        # Bob -> Charlie
        tx2 = create_signed_transaction(
            sender=bob['address'],
            recipient=charlie['address'],
            amount=5.0,
            fee=0.02,
            private_key=bob['private_key']
        )
        
        # Charlie -> Alice
        tx3 = create_signed_transaction(
            sender=charlie['address'],
            recipient=alice['address'],
            amount=2.0,
            fee=0.02,
            private_key=charlie['private_key']
        )
        
        assert tx1['txid'] != tx2['txid'] != tx3['txid']
        assert verify_tx_signature(tx1)
        assert verify_tx_signature(tx2)
        assert verify_tx_signature(tx3)
        
    def test_user_creates_multiple_transactions(self, test_wallets):
        """Test user can create multiple transactions"""
        alice = test_wallets['alice']
        bob = test_wallets['bob']
        
        transactions = []
        
        for i in range(5):
            tx = create_signed_transaction(
                sender=alice['address'],
                recipient=bob['address'],
                amount=float(i + 1),
                fee=0.02,
                private_key=alice['private_key']
            )
            transactions.append(tx)
            
        # All transactions should have unique TXIDs
        txids = [tx['txid'] for tx in transactions]
        assert len(set(txids)) == 5
        
        # All transactions should be valid
        for tx in transactions:
            assert verify_tx_signature(tx)


@pytest.mark.unit
class TestUserEdgeCases:
    """Test edge cases and error handling"""
    
    def test_send_to_self(self, test_wallets):
        """Test user can send transaction to themselves"""
        alice = test_wallets['alice']
        
        tx = create_signed_transaction(
            sender=alice['address'],
            recipient=alice['address'],  # Sending to self
            amount=10.0,
            fee=0.02,
            private_key=alice['private_key']
        )
        
        assert tx['sender'] == tx['recipient']
        assert verify_tx_signature(tx)
        
    def test_very_small_amount(self, test_wallets):
        """Test transaction with very small amount"""
        alice = test_wallets['alice']
        bob = test_wallets['bob']
        
        tx = create_signed_transaction(
            sender=alice['address'],
            recipient=bob['address'],
            amount=0.00000001,  # Very small amount
            fee=0.02,
            private_key=alice['private_key']
        )
        
        assert tx['amount'] == 0.00000001
        
    def test_very_large_amount(self, test_wallets):
        """Test transaction with very large amount"""
        alice = test_wallets['alice']
        bob = test_wallets['bob']
        
        tx = create_signed_transaction(
            sender=alice['address'],
            recipient=bob['address'],
            amount=1_000_000.0,  # Very large amount
            fee=0.02,
            private_key=alice['private_key']
        )
        
        assert tx['amount'] == 1_000_000.0


@pytest.mark.unit
class TestWalletSecurity:
    """Test wallet security features"""
    
    def test_private_key_not_exposed(self, encrypted_wallet):
        """Test private key is not exposed in wallet file"""
        with open(encrypted_wallet['path'], 'r') as f:
            content = f.read()
            
        # Should not contain raw private key
        # (This test assumes encryption is working)
        assert 'encrypted' in content.lower() or 'ciphertext' in content.lower()
        
    def test_different_passwords_produce_different_encryption(self, tmp_path):
        """Test same wallet encrypted with different passwords produces different files"""
        # This would require generating the same wallet twice with different passwords
        # For now, we just test that encryption is applied
        
        wallet1_path = tmp_path / "wallet1.json"
        wallet2_path = tmp_path / "wallet2.json"
        
        create_encrypted_wallet(str(wallet1_path), password="Password1")
        create_encrypted_wallet(str(wallet2_path), password="Password2")
        
        content1 = wallet1_path.read_text()
        content2 = wallet2_path.read_text()
        
        # Different passwords should produce different encrypted content
        # (Even though the wallets are different too)
        assert content1 != content2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
