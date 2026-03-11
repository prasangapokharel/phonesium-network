# Phonesium Network (PHN)

> A production-ready blockchain built from scratch in Python with enterprise-grade security.

[![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Build](https://img.shields.io/badge/Build-Passing-brightgreen?style=flat-square)]()

## Overview

PHN (Phonesium Network) implements every major security feature found in Bitcoin and Ethereum, plus additional protections against modern attack vectors.

## Features

- Proof-of-Work (PoW) consensus
- Wallet creation & management
- Token minting and transfers
- Enterprise-grade security
- Full test suite with pytest
- REST API via FastAPI

## Project Structure

```
phonesium-network/
├── phonesium/     # Core blockchain engine
├── app/           # REST API (FastAPI)
├── user/          # Wallet management
├── docs/          # Documentation
└── test/          # Test suite
```

## Getting Started

```bash
git clone https://github.com/prasangapokharel/phonesium-network.git
cd phonesium-network
pip install -r requirements.txt
python -m phonesium
```

## Running Tests

```bash
pytest
```

## License

MIT License — © 2025 Prasanga Pokharel
