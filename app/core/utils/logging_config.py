"""
Logging configuration for PHN Blockchain
"""

import logging
import logging.handlers
import os
from pathlib import Path

# Create logs directory if it doesn't exist
LOGS_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)


def setup_logging(name: str = "phn_blockchain", level: str = None):
    """
    Setup logging with file rotation and proper formatting

    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
               If None, uses LOG_LEVEL from environment or INFO
    """
    # Get log level from environment or default to INFO
    if level is None:
        level = os.getenv("LOG_LEVEL", "INFO").upper()

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level))

    # Remove existing handlers
    logger.handlers.clear()

    # Console handler with color support
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)  # Console shows INFO and above
    console_formatter = logging.Formatter("[%(levelname)s] %(message)s")
    console_handler.setFormatter(console_formatter)

    # File handler with rotation (10MB max, keep 5 backups)
    file_handler = logging.handlers.RotatingFileHandler(
        LOGS_DIR / f"{name}.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
    )
    file_handler.setLevel(logging.DEBUG)  # File logs everything
    file_formatter = logging.Formatter(
        "[%(asctime)s] [%(name)s] [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)

    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


# Create default logger
logger = setup_logging()
