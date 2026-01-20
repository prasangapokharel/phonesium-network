"""
Phonesium Exceptions
"""

class PhonesiumError(Exception):
    """Base exception for all Phonesium errors"""
    pass

class NetworkError(PhonesiumError):
    """Network connection or API error"""
    pass

class InsufficientBalanceError(PhonesiumError):
    """Insufficient balance for transaction"""
    pass

class InvalidTransactionError(PhonesiumError):
    """Transaction validation failed"""
    pass

class InvalidAddressError(PhonesiumError):
    """Invalid PHN address format"""
    pass

class WalletError(PhonesiumError):
    """Wallet creation or loading error"""
    pass
