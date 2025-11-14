import os
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional
from stellar_service import StellarService

API_SECRET_KEY = os.getenv("API_SECRET_KEY", "your-api-key-here")
FEE_WALLET_ADDRESS = os.getenv("FEE_WALLET_ADDRESS", None)
QOIN_CODE = "QOIN"

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or restrict for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

stellar = StellarService()

class CreateWalletRequest(BaseModel):
    user_id: Optional[str]
    email: Optional[EmailStr]

class DepositRequest(BaseModel):
    wallet_address: str
    amount: float

class SendRequest(BaseModel):
    from_address: str
    to_address: str
    amount: float
    secret_key: str

class WithdrawRequest(BaseModel):
    wallet_address: str
    amount: float
    secret_key: str

async def verify_api_key(x_api_key: str = Header(None)):
    if not x_api_key or x_api_key != API_SECRET_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "qoin-wallet-api"}

@app.post("/api/wallet/create")
async def create_wallet(_: CreateWalletRequest, api_key: str = Depends(verify_api_key)):
    try:
        keys = await stellar.create_and_trust_wallet()
        return {
            "success": True,
            "wallet_address": keys['public_key'],
            "secret_key": keys['secret_key'],
            "message": "Wallet created, funded, and trustline established."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/deposit")
async def deposit_and_mint(request: DepositRequest, api_key: str = Depends(verify_api_key)):
    try:
        tx_hash = await stellar.mint_tokens(request.wallet_address, request.amount)
        return {
            "success": True,
            "tx_hash": tx_hash,
            "amount_minted": request.amount,
            "new_balance": await stellar.get_balance(request.wallet_address)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/send")
async def send_qoins(request: SendRequest, api_key: str = Depends(verify_api_key)):
    try:
        fee = request.amount * 0.01
        recipient_amount = request.amount - fee
        tx_hash = await stellar.send_payment(request.secret_key, request.to_address, recipient_amount)
        if fee > 0 and FEE_WALLET_ADDRESS:
            await stellar.send_payment(request.secret_key, FEE_WALLET_ADDRESS, fee)
        return {
            "success": True,
            "tx_hash": tx_hash,
            "amount_sent": recipient_amount,
            "fee_charged": fee,
            "new_balance": await stellar.get_balance(request.from_address)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/withdraw")
async def withdraw_and_burn(request: WithdrawRequest, api_key: str = Depends(verify_api_key)):
    try:
        tx_hash = await stellar.burn_tokens(request.secret_key, request.amount)
        return {
            "success": True,
            "tx_hash": tx_hash,
            "amount_burned": request.amount,
            "new_balance": await stellar.get_balance(request.wallet_address)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/balance/{wallet_address}")
async def get_balance(wallet_address: str):
    try:
        balance = await stellar.get_balance(wallet_address)
        return {
            "wallet_address": wallet_address,
            "balance_db": balance,
            "currency": QOIN_CODE
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
