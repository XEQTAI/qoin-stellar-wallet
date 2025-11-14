import os
import requests

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL", "no-reply@yourdomain.com")  # Use a verified sender

def send_email(to_email: str, subject: str, html_body: str):
    if not SENDGRID_API_KEY:
        print("SendGrid API key missing. Not sending email.")
        return
    data = {
        "personalizations": [
            { "to": [ { "email": to_email } ] }
        ],
        "from": { "email": FROM_EMAIL },
        "subject": subject,
        "content": [ { "type": "text/html", "value": html_body } ],
    }
    response = requests.post(
        "https://api.sendgrid.com/v3/mail/send",
        headers={
            "Authorization": f"Bearer {SENDGRID_API_KEY}",
            "Content-Type": "application/json"
        },
        json=data
    )
    if response.status_code != 202:
        print("Email failed:", response.text)
3️⃣ main.py
Paste this as your ENTIRE main.py for a working system with wallet emails and balance change alerts:

import os
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional
from stellar_service import StellarService
from email_utils import send_email

API_SECRET_KEY = os.getenv("API_SECRET_KEY", "your-api-key-here")
FEE_WALLET_ADDRESS = os.getenv("FEE_WALLET_ADDRESS", None)
QOIN_CODE = "QOIN"

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace for production
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
    email: Optional[EmailStr] = None

class SendRequest(BaseModel):
    from_address: str
    to_address: str
    amount: float
    secret_key: str
    email: Optional[EmailStr] = None

class WithdrawRequest(BaseModel):
    wallet_address: str
    amount: float
    secret_key: str
    email: Optional[EmailStr] = None

async def verify_api_key(x_api_key: str = Header(None)):
    if not x_api_key or x_api_key != API_SECRET_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "qoin-wallet-api"}

@app.post("/api/wallet/create")
async def create_wallet(request: CreateWalletRequest, api_key: str = Depends(verify_api_key)):
    try:
        keys = await stellar.create_and_trust_wallet()
        # Send wallet creation email
        if request.email:
            send_email(
                to_email=request.email,
                subject="Welcome to QOIN – Your Wallet Details",
                html_body=f"""
                    <h2>Welcome to QOIN!</h2>
                    <p>Your new Stellar wallet has been created.</p>
                    <strong>Wallet Address:</strong><br>
                    <code>{keys['public_key']}</code><br>
                    <strong>Secret Key (KEEP SAFE!):</strong><br>
                    <code>{keys['secret_key']}</code>
                    <p style="color:red;">Never share your secret key. Save this email. <br>Your secret key cannot be recovered!</p>
                """)
        return {
            "success": True,
            "wallet_address": keys['public_key'],
            "secret_key": keys['secret_key'],
            "message": "Wallet created, funded, trustline established, and emailed."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Helper to lookup user email: you may want to save user_id/email in DB and look it up here
def get_user_email(wallet_address: str, fallback: Optional[str] = None):
    # If you have a DB lookup, use it!
    return fallback  # For now

@app.post("/api/deposit")
async def deposit_and_mint(request: DepositRequest, api_key: str = Depends(verify_api_key)):
    try:
        tx_hash = await stellar.mint_tokens(request.wallet_address, request.amount)
        new_balance = await stellar.get_balance(request.wallet_address)
        user_email = request.email or get_user_email(request.wallet_address)
        if user_email:
            send_email(
                to_email=user_email,
                subject="QOIN Balance Update!",
                html_body=f"""
                    <h2>Your QOIN Balance Just Changed!</h2>
                    <p>New balance for <code>{request.wallet_address}</code>:</p>
                    <strong>{new_balance} QOIN</strong>
                """
            )
        return {
            "success": True,
            "tx_hash": tx_hash,
            "amount_minted": request.amount,
            "new_balance": new_balance
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
        sender_balance = await stellar.get_balance(request.from_address)
        recipient_balance = await stellar.get_balance(request.to_address)
        user_email = request.email or get_user_email(request.from_address)
        recipient_email = get_user_email(request.to_address)
        if user_email:
            send_email(
                to_email=user_email,
                subject="QOIN Balance Update (SENT)",
                html_body=f"""Your new QOIN balance: <strong>{sender_balance} QOIN</strong>"""
            )
        if recipient_email:
            send_email(
                to_email=recipient_email,
                subject="You Received Qoins!",
                html_body=f"""Your new QOIN balance: <strong>{recipient_balance} QOIN</strong>"""
            )
        return {
            "success": True,
            "tx_hash": tx_hash,
            "amount_sent": recipient_amount,
            "fee_charged": fee,
            "new_balance": sender_balance
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/withdraw")
async def withdraw_and_burn(request: WithdrawRequest, api_key: str = Depends(verify_api_key)):
    try:
        tx_hash = await stellar.burn_tokens(request.secret_key, request.amount)
        new_balance = await stellar.get_balance(request.wallet_address)
        user_email = request.email or get_user_email(request.wallet_address)
        if user_email:
            send_email(
                to_email=user_email,
                subject="QOIN Balance Update (Withdrawal)",
                html_body=f"""Your new QOIN balance: <strong>{new_balance} QOIN</strong>"""
            )
        return {
            "success": True,
            "tx_hash": tx_hash,
            "amount_burned": request.amount,
            "new_balance": new_balance
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
