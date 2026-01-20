# PHN Blockchain - Asset Tokenization Guide

**Complete Guide to Real-World Asset Tokenization**

---

## Table of Contents

1. [Introduction](#introduction)
2. [What is Asset Tokenization?](#what-is-asset-tokenization)
3. [Supported Asset Types](#supported-asset-types)
4. [Getting Started](#getting-started)
5. [Asset Creation Examples](#asset-creation-examples)
6. [Real-World Use Cases](#real-world-use-cases)
7. [Advanced Features](#advanced-features)
8. [API Reference](#api-reference)
9. [Best Practices](#best-practices)
10. [Security](#security)

---

## Introduction

PHN Blockchain provides **built-in asset tokenization** capabilities, allowing you to represent real-world assets on the blockchain. This creates a digital twin of physical assets with cryptographic proof of ownership.

### Why Tokenize Assets?

- **Fractional Ownership** - Split expensive assets into affordable shares
- **Instant Trading** - Buy/sell assets 24/7 without intermediaries
- **Provenance Tracking** - Complete history from creation to current owner
- **Reduced Fraud** - Cryptographic signatures prevent counterfeiting
- **Global Access** - Anyone can invest in assets worldwide
- **Lower Costs** - No middlemen, reduced transaction fees

---

## What is Asset Tokenization?

**Asset tokenization** is the process of creating a digital representation of a physical asset on the blockchain. Each token is:

- **Unique** - Has a unique asset ID
- **Owned** - Linked to a specific wallet address
- **Signed** - Cryptographically signed by the owner
- **Immutable** - Cannot be altered once created
- **Transferable** - Can be sent to other addresses
- **Verifiable** - Ownership can be proven mathematically

### How It Works

```
Physical Asset → Digital Token → Blockchain Storage → Ownership Proof
```

1. **Physical Asset** - Real gold bar, land plot, property
2. **Create Token** - Generate digital representation with metadata
3. **Sign with Wallet** - Cryptographically link to your address
4. **Store on Blockchain** - Immutable record of ownership
5. **Transfer/Trade** - Send to buyers, maintain history

---

## Supported Asset Types

PHN Blockchain supports 6 primary asset types:

### 1. GOLD
Precious metal tokenization with multiple units:
- **troy_oz** - Troy ounces (31.1g)
- **g** - Grams
- **kg** - Kilograms

**Use Cases:**
- Gold bars (physical vault storage)
- Gold coins (numismatic value)
- Gold ETFs (fractional ownership)
- Jewelry backing (authenticity proof)

### 2. LAND
Real estate and land plots:
- **acres** - Acres (43,560 sqft)
- **hectares** - Hectares (10,000 sqm)
- **sqft** - Square feet
- **sqm** - Square meters

**Use Cases:**
- Agricultural land
- Commercial property
- Residential lots
- Undeveloped land

### 3. REAL_ESTATE
Buildings and structures:
- Full properties (houses, apartments)
- Commercial buildings (offices, malls)
- Industrial facilities (warehouses, factories)

**Use Cases:**
- Rental properties (REITs)
- Commercial real estate
- Vacation homes (fractional ownership)
- Development projects

### 4. COMMODITY
Raw materials and resources:
- Oil and gas
- Agricultural products (wheat, corn, soybeans)
- Metals (silver, platinum, copper)
- Energy (renewable energy credits)

### 5. SECURITY
Financial instruments:
- Stocks and bonds
- Derivatives
- Options and futures
- Investment funds

### 6. CUSTOM
Any other asset type:
- Art and collectibles
- Intellectual property
- Carbon credits
- Supply chain items

---

## Getting Started

### Installation

```bash
# PHN Blockchain SDK (Phonesium) is included
# No additional installation needed
```

### Quick Start

```python
from phonesium import AssetCreator, PhonWallet

# Create or load wallet
wallet = PhonWallet.load("my_wallet.json", password="mypassword")

# Initialize asset creator
creator = AssetCreator(wallet)

# Create a gold asset
gold_asset = creator.create_gold(
    quantity=10,
    unit="troy_oz",
    name="Gold Bar - Credit Suisse",
    description="999.9 pure gold bar, Serial: CS-2026-001"
)

print(f"Asset created: {gold_asset['asset_id']}")
print(f"Owner: {gold_asset['owner']}")
print(f"Signature: {gold_asset['signature']}")
```

---

## Asset Creation Examples

### Example 1: Gold Bar (1kg)

```python
from phonesium import AssetCreator, PhonWallet

# Load wallet
wallet = PhonWallet.load("vault_wallet.json", password="secure123")
creator = AssetCreator(wallet)

# Create 1kg gold bar
gold_bar = creator.create_gold(
    quantity=1,
    unit="kg",
    name="PAMP Suisse Gold Bar",
    description="1 kilogram 999.9 fine gold",
    metadata={
        "serial_number": "PAMP-2026-12345",
        "certificate": "ISO-9001-CERTIFIED",
        "vault": "Swiss Bank Vault A7",
        "insurance": {
            "provider": "Lloyd's of London",
            "policy": "GOLD-2026-001",
            "value_usd": 65000
        },
        "audit": {
            "company": "PwC",
            "date": "2026-01-15",
            "report": "AUDIT-2026-Q1"
        }
    }
)

print(f"Gold Asset ID: {gold_bar['asset_id']}")
print(f"Quantity: {gold_bar['quantity']} {gold_bar['unit']}")
```

**Output:**
```
Gold Asset ID: a4264bc6a172e0b6...
Quantity: 1 kg
Owner: PHN82799c8...
Type: GOLD
```

### Example 2: Land Plot (5 Acres)

```python
land_asset = creator.create_land(
    quantity=5,
    unit="acres",
    name="Agricultural Land - Iowa",
    description="Prime farmland with irrigation",
    metadata={
        "location": {
            "state": "Iowa",
            "county": "Polk County",
            "coordinates": "41.5868° N, 93.6250° W"
        },
        "deed_number": "IOWA-2026-45678",
        "zoning": "Agricultural A-1",
        "water_rights": "Included",
        "features": [
            "Irrigation system",
            "Fertile soil",
            "Road access"
        ],
        "valuation": {
            "price_per_acre": 8000,
            "total_value_usd": 40000
        }
    }
)
```

### Example 3: Real Estate REIT (Fractional)

```python
# Create 1000 shares of a property (fractional ownership)
property_shares = creator.create_asset(
    asset_type="REAL_ESTATE",
    quantity=1000,  # 1000 shares
    name="Downtown Office Building - REIT",
    description="Class A office space, 50,000 sqft",
    metadata={
        "property_type": "Commercial Office",
        "total_shares": 1000,
        "share_value_usd": 100,
        "address": "123 Main Street, New York, NY",
        "year_built": 2020,
        "rental_income_annual": 500000,
        "occupancy_rate": 95,
        "tenants": [
            "Tech Corp Inc.",
            "Legal Associates LLC",
            "Financial Services Co."
        ]
    }
)

print(f"Created 1000 shares of real estate REIT")
print(f"Each share represents 0.1% ownership")
print(f"Estimated value per share: $100 USD")
```

### Example 4: Commodity (Oil Barrels)

```python
oil_asset = creator.create_asset(
    asset_type="COMMODITY",
    custom_type="OIL",
    quantity=1000,
    name="Crude Oil Futures",
    description="West Texas Intermediate (WTI) crude oil",
    metadata={
        "commodity": "Crude Oil",
        "grade": "West Texas Intermediate",
        "quantity_barrels": 1000,
        "contract_month": "March 2026",
        "storage_location": "Cushing, Oklahoma",
        "quality_specs": {
            "api_gravity": 40,
            "sulfur_content": "0.3%"
        }
    }
)
```

### Example 5: Custom Asset (Fine Art)

```python
art_asset = creator.create_asset(
    asset_type="CUSTOM",
    custom_type="FINE_ART",
    quantity=1,
    name="Abstract Painting - 'Sunrise'",
    description="Original oil painting by renowned artist",
    metadata={
        "artist": "Jane Smith",
        "year": 2025,
        "medium": "Oil on canvas",
        "dimensions": "48x36 inches",
        "provenance": [
            "2025: Created by artist",
            "2025-06: Sold at Sotheby's auction",
            "2026-01: Current owner"
        ],
        "certification": {
            "authenticator": "Art Authentication Inc.",
            "certificate_number": "ART-2025-7890",
            "appraisal_value_usd": 50000
        },
        "insurance": {
            "provider": "Fine Art Insurance Co.",
            "policy": "ART-2026-002"
        }
    }
)
```

---

## Real-World Use Cases

### Use Case 1: Gold Vault Tokenization

**Scenario:** Swiss bank wants to tokenize physical gold stored in vaults

```python
# Bank creates asset creator
bank_wallet = PhonWallet.load("bank_vault.json", password="bank_secure")
vault_creator = AssetCreator(bank_wallet)

# Tokenize 100 gold bars (1kg each)
gold_bars = []
for i in range(1, 101):
    bar = vault_creator.create_gold(
        quantity=1,
        unit="kg",
        name=f"Swiss Bank Gold Bar #{i}",
        description="999.9 fine gold, vault stored",
        metadata={
            "serial": f"SWISS-2026-{i:05d}",
            "vault": "Vault A",
            "insurance_value_usd": 65000,
            "audit_date": "2026-01-20"
        }
    )
    gold_bars.append(bar)

print(f"Tokenized 100 gold bars (100 kg total)")
print(f"Total value: ~$6.5M USD")
```

**Benefits:**
- Customers can buy fractional gold (0.1kg, 0.01kg)
- Instant trading 24/7
- Proof of ownership via blockchain
- Reduced storage/handling costs

### Use Case 2: Agricultural Land Investment

**Scenario:** Farmers tokenize land for fractional investment

```python
# Farmer tokenizes 100 acres
farmer_wallet = PhonWallet.load("farmer.json", password="farm123")
farmer_creator = AssetCreator(farmer_wallet)

# Create 1000 shares (each = 0.1 acre)
farm_shares = farmer_creator.create_land(
    quantity=1000,
    unit="acres",
    name="Johnson Farm - Investment Shares",
    description="Prime Iowa farmland - fractional ownership",
    metadata={
        "total_acres": 100,
        "shares": 1000,
        "price_per_share_usd": 800,
        "annual_yield": "Corn and Soybeans",
        "profit_sharing": "Pro-rata to shareholders"
    }
)

print("Created 1000 shares of farmland")
print("Minimum investment: $800 (1 share = 0.1 acre)")
```

**Benefits:**
- Small investors can own farmland
- Diversification for farmers
- Transparent profit sharing
- Easy transfer of ownership

### Use Case 3: Real Estate REITs

**Scenario:** Property management company creates REIT on blockchain

```python
# Property manager tokenizes building
pm_wallet = PhonWallet.load("property_mgmt.json", password="pm_secure")
reit_creator = AssetCreator(pm_wallet)

# Create 10,000 REIT shares
reit = reit_creator.create_asset(
    asset_type="REAL_ESTATE",
    quantity=10000,
    name="Manhattan Office Tower REIT",
    description="Class A+ office building, 30 floors",
    metadata={
        "property_value_usd": 50000000,
        "total_shares": 10000,
        "price_per_share_usd": 5000,
        "dividend_yield_annual": "6%",
        "dividend_frequency": "Quarterly",
        "management_fee": "2%"
    }
)

print("REIT created: 10,000 shares @ $5,000 each")
print("Total property value: $50M")
print("Annual dividends: 6% yield")
```

**Benefits:**
- Democratized real estate investment
- Instant liquidity (vs traditional REITs)
- Lower minimum investment
- Transparent on-chain dividends

### Use Case 4: Supply Chain Tracking

**Scenario:** Coffee producer tracks beans from farm to consumer

```python
# Coffee producer tokenizes batch
producer_wallet = PhonWallet.load("coffee_producer.json", password="coffee123")
supply_creator = AssetCreator(producer_wallet)

# Tokenize coffee batch
coffee_batch = supply_creator.create_asset(
    asset_type="COMMODITY",
    custom_type="COFFEE",
    quantity=1000,
    name="Ethiopian Yirgacheffe - Batch 2026-01",
    description="Single-origin coffee beans",
    metadata={
        "origin": {
            "country": "Ethiopia",
            "region": "Yirgacheffe",
            "farm": "Kochere Cooperative"
        },
        "harvest_date": "2026-01-10",
        "processing": "Washed",
        "grade": "Grade 1",
        "certifications": ["Fair Trade", "Organic"],
        "quantity_kg": 1000,
        "quality_score": 88
    }
)

# Track journey
# Farm → Exporter → Importer → Roaster → Cafe → Consumer
```

**Benefits:**
- Complete traceability
- Proof of authenticity
- Fair trade verification
- Quality assurance

---

## Advanced Features

### 1. Fractional Ownership

Split expensive assets into affordable shares:

```python
# 1 oz gold bar split into 100 shares
fractional_gold = creator.create_gold(
    quantity=100,  # 100 shares
    unit="troy_oz",
    name="Fractional Gold - 1 oz split into 100 shares",
    metadata={
        "total_weight_oz": 1,
        "shares": 100,
        "weight_per_share_g": 0.311  # 31.1g / 100
    }
)
```

### 2. Complex Metadata

Store detailed asset information:

```python
complex_asset = creator.create_asset(
    asset_type="REAL_ESTATE",
    quantity=1,
    name="Luxury Villa",
    metadata={
        "property": {
            "type": "Residential",
            "bedrooms": 5,
            "bathrooms": 4,
            "sqft": 5000,
            "year_built": 2022
        },
        "financials": {
            "purchase_price": 2000000,
            "mortgage": {
                "amount": 1500000,
                "rate": 4.5,
                "term_years": 30
            },
            "taxes_annual": 25000,
            "insurance_annual": 5000
        },
        "location": {
            "address": "123 Ocean View",
            "city": "Miami",
            "state": "FL",
            "zip": "33139"
        },
        "features": [
            "Ocean view",
            "Pool",
            "Smart home"
        ]
    }
)
```

### 3. Multi-Asset Portfolio

Create multiple assets efficiently:

```python
# Create diversified portfolio
portfolio = []

# Add 10 oz gold
portfolio.append(creator.create_gold(10, "troy_oz", "Gold Reserve"))

# Add 50 acres land
portfolio.append(creator.create_land(50, "acres", "Farmland Investment"))

# Add 100 REIT shares
portfolio.append(creator.create_asset(
    "REAL_ESTATE", 100, "Office REIT Shares"
))

print(f"Portfolio created: {len(portfolio)} assets")
```

---

## API Reference

### AssetCreator Class

```python
class AssetCreator:
    def __init__(self, wallet: PhonWallet)
```

### Methods

#### create_gold()
```python
def create_gold(
    quantity: float,
    unit: str,  # "troy_oz", "g", "kg"
    name: str,
    description: str = "",
    metadata: dict = None
) -> dict
```

#### create_land()
```python
def create_land(
    quantity: float,
    unit: str,  # "acres", "hectares", "sqft", "sqm"
    name: str,
    description: str = "",
    metadata: dict = None
) -> dict
```

#### create_asset()
```python
def create_asset(
    asset_type: str,  # "GOLD", "LAND", "REAL_ESTATE", etc.
    quantity: float,
    name: str,
    description: str = "",
    unit: str = "",
    custom_type: str = "",
    metadata: dict = None
) -> dict
```

### Return Value

All methods return a dictionary:

```python
{
    "asset_id": "a4264bc6a172e0b6...",  # Unique asset ID
    "owner": "PHN82799c8...",           # Wallet address
    "asset_type": "GOLD",                # Asset type
    "quantity": 10.0,                    # Amount
    "unit": "troy_oz",                   # Unit
    "name": "Gold Bar",                  # Name
    "description": "999.9 fine gold",    # Description
    "metadata": {...},                   # Custom data
    "timestamp": 1737395520,             # Creation time
    "signature": "304402..."             # ECDSA signature
}
```

---

## Best Practices

### 1. Always Use Metadata
Store comprehensive information:
```python
metadata={
    "serial_number": "...",
    "certificate": "...",
    "insurance": {...},
    "valuation": {...},
    "audit": {...}
}
```

### 2. Fractional Ownership Strategy
For expensive assets, create shares:
```python
# Instead of: 1 asset @ $1M
# Create: 1000 shares @ $1,000 each
```

### 3. Clear Naming Convention
Use descriptive names:
```python
name="Gold Bar - Credit Suisse 1kg - Serial CS-2026-001"
# NOT: "Gold 1"
```

### 4. Backup Asset IDs
Store asset IDs securely:
```python
asset_id = gold_asset['asset_id']
# Save to database, file, or secure storage
```

### 5. Verify Signatures
Always verify asset authenticity:
```python
# Signature can be verified by anyone
# Proves ownership and prevents tampering
```

---

## Security

### Cryptographic Signing
Every asset is signed with ECDSA:
- **Algorithm:** SECP256k1 (same as Bitcoin)
- **Signature:** Unique per asset
- **Verification:** Anyone can verify ownership

### Asset ID Generation
Unique IDs prevent collisions:
- **Method:** Hash(owner + type + quantity + timestamp + nonce)
- **Uniqueness:** Timestamp ensures no duplicates
- **Immutability:** Cannot change after creation

### Ownership Proof
Prove ownership mathematically:
```python
# Asset signature proves:
# 1. Created by specific wallet
# 2. Not altered since creation
# 3. Owned by address in 'owner' field
```

### Best Security Practices
1. **Encrypt wallets** with strong passwords
2. **Backup asset data** to multiple locations
3. **Store private keys** securely (never share)
4. **Verify signatures** before trusting assets
5. **Use metadata** to store proof documents

---

## Testing

PHN Asset module has passed **15/15 military-grade stress tests**:

✅ All unit types (gold, land)  
✅ Fractional assets (1000+ shares)  
✅ Complex metadata (nested JSON)  
✅ Extreme values (0.001g to 1M kg)  
✅ Special characters (Unicode, emoji)  
✅ Concurrent creation (50 assets)  
✅ Rapid creation (68.7 assets/second)  
✅ Asset ID collision resistance  
✅ Signature verification  
✅ Ownership uniqueness  

See [STRESS_TEST_RESULTS.md](../military/STRESS_TEST_RESULTS.md) for details.

---

## Examples Repository

Complete working examples:
- `test/unit/test_assets.py` - Basic asset tests
- `test/stress/test_assets_stress.py` - Stress tests
- `phonesium/core/assets.py` - Implementation

---

## Support

For questions and issues:
- GitHub: https://github.com/prasangapokharel/Blockchain/issues
- Documentation: `docs/` directory
- API Reference: `docs/api/SDK_API_REFERENCE.md`

---

## License

MIT License - Free to use for any purpose

---

*Asset Tokenization - Bringing Real-World Assets On-Chain*
