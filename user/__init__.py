"""
PHN Blockchain - User Tools & Utilities

This package contains CLI tools and utilities for end users to interact
with the PHN blockchain network.

Modules:
    cli: Command-line interface tools for common operations
    servers: Server applications (tunnel server, etc.)
    data: User data storage (wallets, files)

Usage:
    # Run CLI tools
    python -m user.cli.create_wallet
    python -m user.cli.check_balance
    python -m user.cli.send_tokens
    python -m user.cli.miner
    
    # Or run directly
    cd user/cli
    python create_wallet.py
"""

__version__ = "1.0.0"
__all__ = ["cli", "servers"]
