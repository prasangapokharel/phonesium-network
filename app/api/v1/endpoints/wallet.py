# wallet.py - Wallet generation API endpoints
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.utils.wallet_generator import (
    generate_new_wallet, generate_multiple_wallets, 
    get_wallet_by_address, get_wallet_by_number,
    list_all_wallets, get_wallet_count
)
from app.core.blockchain.chain import get_balance

router = APIRouter()

class WalletResponse(BaseModel):
    address_number: Optional[int] = None
    private_key: str
    public_key: str
    address: str
    balance: float
    created_at: Optional[str] = None
    label: Optional[str] = None

class GenerateWalletRequest(BaseModel):
    count: Optional[int] = 1
    label: Optional[str] = None
    save_to_db: Optional[bool] = True

class WalletListResponse(BaseModel):
    address_number: int
    address: str
    balance: float
    created_at: Optional[str] = None
    label: Optional[str] = None

@router.post("/generate", response_model=WalletResponse)
async def generate_wallet(label: Optional[str] = None):
    """Generate a new PHN wallet and save to database"""
    try:
        wallet = generate_new_wallet(label=label, save_to_db=True)
        
        # Get current balance from blockchain
        wallet['balance'] = get_balance(wallet['address'])
        
        return WalletResponse(**wallet)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate wallet: {str(e)}")

@router.post("/generate-multiple", response_model=List[WalletResponse])
async def generate_multiple_wallets_endpoint(request: GenerateWalletRequest):
    """Generate multiple PHN wallets and save to database"""
    try:
        if request.count < 1 or request.count > 100:
            raise HTTPException(status_code=400, detail="Count must be between 1 and 100")
        
        wallets = generate_multiple_wallets(request.count, save_to_db=request.save_to_db)
        
        # Get current balances from blockchain
        for wallet in wallets:
            wallet['balance'] = get_balance(wallet['address'])
        
        return [WalletResponse(**wallet) for wallet in wallets]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate wallets: {str(e)}")

@router.get("/list", response_model=List[WalletListResponse])
async def list_wallets():
    """List all wallets from database"""
    try:
        wallets = list_all_wallets()
        
        # Get current balances from blockchain
        for wallet in wallets:
            wallet['balance'] = get_balance(wallet['address'])
        
        return [WalletListResponse(**wallet) for wallet in wallets]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list wallets: {str(e)}")

@router.get("/count")
async def get_total_wallet_count():
    """Get total number of wallets in database"""
    try:
        count = get_wallet_count()
        return {"total_wallets": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get wallet count: {str(e)}")

@router.get("/{address}", response_model=WalletResponse)
async def get_wallet(address: str):
    """Get wallet by PHN address"""
    try:
        if not address.startswith("PHN") or len(address) != 43:
            raise HTTPException(status_code=400, detail="Invalid PHN address format")
        
        wallet = get_wallet_by_address(address)
        if not wallet:
            raise HTTPException(status_code=404, detail="Wallet not found")
        
        # Get current balance from blockchain
        wallet['balance'] = get_balance(wallet['address'])
        
        return WalletResponse(**wallet)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get wallet: {str(e)}")

@router.get("/number/{address_number}", response_model=WalletResponse)
async def get_wallet_by_number_endpoint(address_number: int):
    """Get wallet by address number"""
    try:
        wallet = get_wallet_by_number(address_number)
        if not wallet:
            raise HTTPException(status_code=404, detail="Wallet not found")
        
        # Get current balance from blockchain
        wallet['balance'] = get_balance(wallet['address'])
        
        return WalletResponse(**wallet)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get wallet: {str(e)}")

@router.get("/balance/{address}")
async def get_wallet_balance(address: str):
    """Get balance for a PHN address"""
    try:
        if not address.startswith("PHN") or len(address) != 43:
            raise HTTPException(status_code=400, detail="Invalid PHN address format")
        
        balance = get_balance(address)
        return {"address": address, "balance": balance}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get balance: {str(e)}")
