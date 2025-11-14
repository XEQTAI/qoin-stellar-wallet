import os
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from stellar_sdk import Server, Keypair, TransactionBuilder, Network, Asset, NotFoundError
from typing import Optional

# ---- QOIN CONFIG ----
QOIN_CODE = "QOIN"
QOIN_ISSUER = "GDRCM33AI6O6LVMPTN5NGKQS57VBQGAVA7J6VVSIT6PO5XFKEQLODHSO"  # Your QOIN issuer key
STELLAR_NETWORK = os.getenv("STELLAR_NETWORK", "testnet")

# ---- STELLAR SERVICE ----
class StellarService:
    def __init__(self):
        if STELLAR_NETWORK == "mainnet":
            self.server = Server("https://horizon.stellar.org")
            self.network_passphrase = Network.PUBLIC_NETWORK_PASSPHRASE
        else:
            self.server = Server("https://horizon-testnet.stellar.org")
            self.network_passphrase = Network.TESTNET_NETWORK_PASSPHRASE

        issuer_secret = os.getenv("ISSUER_SECRET_KEY")
        self.issuer_keypair = Keypair.from_secret(issuer_secret) if issuer_secret else None
        self.qoin_asset = Asset(QOIN_CODE, QOIN_ISSUER)

    async def create_and_trust_wallet(self):
        kp = Keypair.random()
        if STELLAR_NETWORK == "testnet":
            import requests
            r = requests.get(f"https://friendbot.stellar.org?addr={kp.public_key}")
            if r.status_code != 200:
                raise Exception("Friendbot funding failed!")
        account = self.server.load_account(kp.public_key)
        tx = (
            TransactionBuilder(account, self.network_passphrase, base_fee=100)
            .append_change_trust_op(asset=self.qoin_asset)
            .set_timeout(30)
            .build()
        )
        tx.sign(kp)
        self.server.submit_transaction(tx)
        return {"public_key": kp.public_key, "secret_key": kp.secret}

    async def mint_tokens(self, destination: str, amount: float):
        issuer_account = self.server.load_account(self.issuer_keypair.public_key)
        tx = (
            TransactionBuilder(issuer_account, self.network_passphrase, base_fee=100)
            .append_payment_op(destination, self.qoin_asset, str(amount))
            .set_timeout(30).build()
        )
        tx.sign(self.issuer_keypair)
        response = self.server.submit_transaction(tx)
        return response['hash']

    async def send_payment(self, from_secret: str, to_address: str, amount: float):
        sender_kp = Keypair.from_secret(from_secret)
        sender_account = self.server.load_account(sender_kp.public_key)
        tx = (
            TransactionBuilder(sender_account, self.network_passphrase, base_fee=100)
            .append_payment_op(to_address, self.qoin_asset, str(amount))
            .set_timeout(30).build()
        )
        tx.sign(sender_kp)
        response = self.server.submit_transaction(tx)
        return response['hash']

    async def burn_tokens(self, from_secret: str, amount: float):
        sender_kp = Keypair.from_secret(from_secret)
        account = self.server.load_account(sender_kp.public_key)
        tx = (
            TransactionBuilder(account, self.network_passphrase, base_fee=100)
            .append_payment_op(self.issuer_keypair.public_key, self.qoin_asset, str(amount))
            .set_timeout(30).build()
        )
        tx.sign(sender_kp)
        response = self.server.submit_transaction(tx)
        return response['hash']

    async def get_balance(self, address: str) -> float:
        try:
            acc = self.server.accounts().account_id(address).call()
            for b in acc['balances']:
                if b.get('asset_code') == QOIN_CODE and b.get('asset_issuer') == QOIN_ISSUER:
                    return float(b['balance'])
            return 0.0
        except NotFoundError:
            return 0.0

# ---- FASTAPI APP & MODELS ----

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify your Netlify URL for security
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
    expected_key = os.getenv("API_SECRET_KEY")
    if not x_api_key or x_api_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "qoin-wallet-api"}

@app.post("/api/wallet/create")
async def create_wallet(request: CreateWalletRequest, api_key: str = Depends(verify_api_key)):
    try:
        keys = await stellar.create_and_trust_wallet()
        # Add your DB storage here if needed
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
        tx_hash = await stellar.send_payment(request.from_address, request.to_address, recipient_amount)
        fee_wallet = os.getenv("FEE_WALLET_ADDRESS")
        if fee > 0 and fee_wallet:
            await stellar.send_payment(request.from_address, fee_wallet, fee)
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
