"""
Setup script for Phonesium SDK
Python library for interacting with PHN Blockchain
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
this_directory = Path(__file__).parent
long_description = ""
readme_file = this_directory / "README.md"
if readme_file.exists():
    long_description = readme_file.read_text(encoding="utf-8")

setup(
    name="phonesium",
    version="1.0.0",
    author="Phonesium Team",
    author_email="support@phonesium.network",
    description="Python SDK for PHN Blockchain - Easy wallet management, transactions, and mining",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/phonesium/phonesium-sdk",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Security :: Cryptography",
        "Topic :: Office/Business :: Financial",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
    python_requires=">=3.8",
    install_requires=[
        "orjson>=3.9.0",
        "requests>=2.31.0",
        "ecdsa>=0.18.0",
        "cryptography>=41.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.7.0",
            "flake8>=6.1.0",
            "mypy>=1.5.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "phonesium-wallet=phonesium.core.wallet:main",
            "phonesium-miner=phonesium.core.miner:main",
        ],
    },
    keywords="blockchain cryptocurrency wallet phn phonesium sdk",
    project_urls={
        "Documentation": "https://docs.phonesium.network",
        "Source": "https://github.com/phonesium/phonesium-sdk",
        "Bug Reports": "https://github.com/phonesium/phonesium-sdk/issues",
    },
)
