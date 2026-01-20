"""
Test Helper Functions
Helper functions for creating test data
"""
from app.core.transactions.base import create_transaction, generate_keypair, generate_address_from_public_key


def create_test_wallet():
    """Generate a wallet for testing"""
    private_key, public_key, address = generate_keypair()
    
    return {
        'private_key': private_key,
        'public_key': public_key,
        'address': address
    }


def create_signed_transaction(sender, recipient, amount, fee, private_key):
    """
    Create and sign a transaction for testing
    
    Args:
        sender: dict with 'address', 'public_key', 'private_key'
        recipient: dict with 'address' or just address string
        amount: float
        fee: float
        private_key: sender's private key
        
    Returns:
        Signed transaction dict
    """
    recipient_addr = recipient if isinstance(recipient, str) else recipient['address']
    sender_public_key = sender if isinstance(sender, str) else sender.get('public_key', sender['address'])
    
    # Get sender's public key from sender dict or use address
    if isinstance(sender, dict):
        sender_public_key = sender.get('public_key', sender['address'])
        sender_private_key = sender.get('private_key', private_key)
    else:
        sender_public_key = sender
        sender_private_key = private_key
        
    tx = create_transaction(
        sender_private_key=sender_private_key,
        sender_public_key=sender_public_key,
        recipient_address=recipient_addr,
        amount=amount,
        fee=fee
    )
    
    return tx


def mine_block_simple(block, difficulty=1):
    """
    Simple mining function for testing
    
    Args:
        block: Block dict
        difficulty: Number of leading zeros required
        
    Returns:
        Mined block with valid hash
    """
    import hashlib
    import orjson
    
    target = '0' * difficulty
    nonce = 0
    max_nonce = 1000000  # Limit for testing
    
    while nonce < max_nonce:
        block['nonce'] = nonce
        
        # Calculate hash
        block_data = {
            'index': block['index'],
            'timestamp': block['timestamp'],
            'transactions': block['transactions'],
            'prev_hash': block['prev_hash'],
            'nonce': nonce
        }
        
        block_string = orjson.dumps(block_data, option=orjson.OPT_SORT_KEYS)
        block_hash = hashlib.sha256(block_string).hexdigest()
        
        if block_hash.startswith(target):
            block['hash'] = block_hash
            return block
            
        nonce += 1
        
    # If we couldn't mine, just return with a hash
    block['hash'] = hashlib.sha256(orjson.dumps(block)).hexdigest()
    return block


def calculate_block_hash(block):
    """Calculate hash of a block"""
    import hashlib
    import orjson
    
    block_data = {
        'index': block['index'],
        'timestamp': block['timestamp'],
        'transactions': block['transactions'],
        'prev_hash': block['prev_hash'],
        'nonce': block.get('nonce', 0)
    }
    
    block_string = orjson.dumps(block_data, option=orjson.OPT_SORT_KEYS)
    return hashlib.sha256(block_string).hexdigest()
