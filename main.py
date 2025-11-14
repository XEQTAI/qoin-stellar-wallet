from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional
import os
from dotenv import load_dotenv

from stellar_service import StellarService
from database import Database

load_dotenv()

app = FastAPI(
    title="Qoin Wallet API",
    description="Deposit-backed token system on Stellar with 1% fees",
    version="1.0.0"
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
stellar = StellarService()
db = Database()

# Request models
class CreateWalletRequest(BaseModel):
    user_id: str
    email: EmailStr

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

# Authentication
async def verify_api_key(x_api_key: str = Header(None)):
    expected_key = os.getenv("API_SECRET_KEY")
    if not x_api_key or x_api_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key

@app.get("/").
@app.head("/")
async def root():
    return {
        "message": "Qoin Wallet API",
        "version": "1.0.0",
        "stellar_network": os.getenv("STELLAR_NETWORK", "testnet"),
        "endpoints": {
            "create_wallet": "/api/wallet/create",
            "deposit": "/api/deposit",
            "send": "/api/send",
            "withdraw": "/api/withdraw",
            "balance": "/api/balance/{address}",
            "transactions": "/api/transactions/{address}"
        }
    }

@app.post("/api/wallet/create")
async def create_wallet(request: CreateWalletRequest, api_key: str = Depends(verify_api_key)):
    '''Create new Stellar wallet for user'''
    try:
        # Generate Stellar keypair
        keypair = stellar.create_keypair()

        # Store in database
        wallet = await db.create_wallet(
            user_id=request.user_id,
            email=request.email,
            stellar_address=keypair['public_key'],
            secret_key=keypair['secret_key']
        )

        return {
            "success": True,
            "wallet_address": keypair['public_key'],
            "message": "Wallet created successfully. Store your secret key safely!",
            "secret_key": keypair['secret_key'],
            "warning": "Save this secret key! It cannot be recovered."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/deposit")
async def deposit_and_mint(request: DepositRequest, api_key: str = Depends(verify_api_key)):
    '''Deposit funds and mint Qoins (1:1 ratio)'''
    try:
        # Verify wallet exists
        wallet = await db.get_wallet_by_address(request.wallet_address)
        if not wallet:
            raise HTTPException(status_code=404, detail="Wallet not found")

        # Mint Qoins on Stellar
        tx_hash = await stellar.mint_tokens(
            destination=request.wallet_address,
            amount=request.amount
        )

        # Update balance in DB
        await db.update_balance(request.wallet_address, request.amount, "add")

        # Record transaction
        await db.create_transaction(
            from_address="ISSUER",
            to_address=request.wallet_address,
            amount=request.amount,
            fee=0,
            tx_hash=tx_hash,
            tx_type="deposit"
        )

        return {
            "success": True,
            "tx_hash": tx_hash,
            "amount_minted": request.amount,
            "new_balance": await db.get_balance(request.wallet_address)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/send")
async def send_qoins(request: SendRequest, api_key: str = Depends(verify_api_key)):
    '''Send Qoins with 1% fee'''
    try:
        # Verify sender wallet
        sender_balance = await db.get_balance(request.from_address)
        if sender_balance < request.amount:
            raise HTTPException(status_code=400, detail="Insufficient balance")

        # Calculate fee (1%)
        fee = request.amount * 0.01
        recipient_amount = request.amount - fee

        # Send on Stellar network
        tx_hash = await stellar.send_payment(
            from_secret=request.secret_key,
            to_address=request.to_address,
            amount=recipient_amount
        )

        # Send fee to fee wallet
        fee_wallet = os.getenv("FEE_WALLET_ADDRESS")
        if fee > 0:
            await stellar.send_payment(
                from_secret=request.secret_key,
                to_address=fee_wallet,
                amount=fee
            )

        # Update balances
        await db.update_balance(request.from_address, request.amount, "subtract")
        await db.update_balance(request.to_address, recipient_amount, "add")

        # Record transaction
        await db.create_transaction(
            from_address=request.from_address,
            to_address=request.to_address,
            amount=request.amount,
            fee=fee,
            tx_hash=tx_hash,
            tx_type="send"
        )

        return {
            "success": True,
            "tx_hash": tx_hash,
            "amount_sent": recipient_amount,
            "fee_charged": fee,
            "new_balance": await db.get_balance(request.from_address)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/withdraw")
async def withdraw_and_burn(request: WithdrawRequest, api_key: str = Depends(verify_api_key)):
    '''Withdraw funds and burn Qoins'''
    try:
        # Verify balance
        balance = await db.get_balance(request.wallet_address)
        if balance < request.amount:
            raise HTTPException(status_code=400, detail="Insufficient balance")

        # Burn tokens on Stellar
        tx_hash = await stellar.burn_tokens(
            from_secret=request.secret_key,
            amount=request.amount
        )

        # Update balance
        await db.update_balance(request.wallet_address, request.amount, "subtract")

        # Record transaction
        await db.create_transaction(
            from_address=request.wallet_address,
            to_address="BURNED",
            amount=request.amount,
            fee=0,
            tx_hash=tx_hash,
            tx_type="withdraw"
        )

        return {
            "success": True,
            "tx_hash": tx_hash,
            "amount_burned": request.amount,
            "amount_withdrawn": request.amount,
            "new_balance": await db.get_balance(request.wallet_address)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/balance/{wallet_address}")
async def get_balance(wallet_address: str):
    '''Get wallet balance'''
    try:
        balance = await db.get_balance(wallet_address)
        stellar_balance = await stellar.get_balance(wallet_address)

        return {
            "wallet_address": wallet_address,
            "balance_db": balance,
            "balance_stellar": stellar_balance,
            "currency": "QOIN"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/transactions/{wallet_address}")
async def get_transactions(wallet_address: str, limit: int = 50):
    '''Get transaction history'''
    try:
        transactions = await db.get_transactions(wallet_address, limit)
        return {
            "wallet_address": wallet_address,
            "transactions": transactions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "qoin-wallet-api"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
