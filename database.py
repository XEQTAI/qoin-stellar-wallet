from supabase import create_client, Client
import os
from typing import Dict, List, Optional
from datetime import datetime
import uuid
from cryptography.fernet import Fernet
import base64

class Database:
    def __init__(self):
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        self.client: Client = create_client(supabase_url, supabase_key)

        # Encryption key for secret keys (you should store this securely!)
        encryption_key = os.getenv("ENCRYPTION_KEY", Fernet.generate_key().decode())
        self.cipher = Fernet(encryption_key.encode())

    def encrypt_secret(self, secret: str) -> str:
        '''Encrypt Stellar secret key'''
        return self.cipher.encrypt(secret.encode()).decode()

    def decrypt_secret(self, encrypted: str) -> str:
        '''Decrypt Stellar secret key'''
        return self.cipher.decrypt(encrypted.encode()).decode()

    async def create_wallet(self, user_id: str, email: str, stellar_address: str, secret_key: str) -> Dict:
        '''Create new wallet in database'''
        encrypted_secret = self.encrypt_secret(secret_key)

        data = {
            "user_id": user_id,
            "email": email,
            "stellar_address": stellar_address,
            "encrypted_secret": encrypted_secret,
            "balance": 0.0
        }

        response = self.client.table("wallets").insert(data).execute()
        return response.data[0] if response.data else None

    async def get_wallet_by_address(self, stellar_address: str) -> Optional[Dict]:
        '''Get wallet by Stellar address'''
        response = self.client.table("wallets").select("*").eq("stellar_address", stellar_address).execute()
        return response.data[0] if response.data else None

    async def get_wallet_by_user(self, user_id: str) -> Optional[Dict]:
        '''Get wallet by user ID'''
        response = self.client.table("wallets").select("*").eq("user_id", user_id).execute()
        return response.data[0] if response.data else None

    async def get_balance(self, stellar_address: str) -> float:
        '''Get wallet balance'''
        wallet = await self.get_wallet_by_address(stellar_address)
        return float(wallet['balance']) if wallet else 0.0

    async def update_balance(self, stellar_address: str, amount: float, operation: str):
        '''Update wallet balance (add or subtract)'''
        wallet = await self.get_wallet_by_address(stellar_address)
        if not wallet:
            raise ValueError("Wallet not found")

        current_balance = float(wallet['balance'])
        if operation == "add":
            new_balance = current_balance + amount
        elif operation == "subtract":
            new_balance = current_balance - amount
        else:
            raise ValueError("Invalid operation")

        if new_balance < 0:
            raise ValueError("Insufficient balance")

        self.client.table("wallets").update({"balance": new_balance}).eq("stellar_address", stellar_address).execute()

    async def create_transaction(self, from_address: str, to_address: str, amount: float, 
                                 fee: float, tx_hash: str, tx_type: str) -> Dict:
        '''Record transaction'''
        data = {
            "from_address": from_address,
            "to_address": to_address,
            "amount": amount,
            "fee": fee,
            "tx_hash": tx_hash,
            "type": tx_type
        }

        response = self.client.table("transactions").insert(data).execute()
        return response.data[0] if response.data else None

    async def get_transactions(self, wallet_address: str, limit: int = 50) -> List[Dict]:
        '''Get transaction history for a wallet'''
        response = self.client.table("transactions") \
            .select("*") \
            .or_(f"from_address.eq.{wallet_address},to_address.eq.{wallet_address}") \
            .order("created_at", desc=True) \
            .limit(limit) \
            .execute()

        return response.data if response.data else []
