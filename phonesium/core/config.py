"""
Phonesium Configuration
Central configuration for the Phonesium SDK
"""

# Default PHN Node Configuration
DEFAULT_NODE_URL = "http://localhost:8765"

# Network Configuration
DEFAULT_TIMEOUT = 10  # seconds

# Tunnel/Communication Configuration
DEFAULT_TUNNEL_HOST = "localhost"
DEFAULT_TUNNEL_PORT = 9999

# Mining Configuration
DEFAULT_MINING_TIMEOUT = 300  # 5 minutes per block

# Request Configuration
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds

# API Endpoints (relative to node URL)
ENDPOINTS = {
    'balance': '/get_balance',
    'send_tx': '/send_tx',
    'blockchain': '/blockchain',
    'info': '/info',
    'mine': '/mine',
    'mempool': '/mempool',
    'peers': '/peers',
    'token_info': '/token_info',
    'mining_info': '/mining_info',
    'create_asset': '/create_asset',
    'asset': '/asset',
    'assets': '/assets'
}

# Version
VERSION = "1.0.0"
AUTHOR = "Phonesium Team"
EMAIL = "support@phonesium.network"
