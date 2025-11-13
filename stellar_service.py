from stellar_sdk import Server, Keypair, TransactionBuilder, Network, Asset, Account
from stellar_sdk.exceptions import NotFoundError, BadRequestError
import os
from typing import Dict
import asyncio

class StellarService:
    def __init__(self):
        self.network = os.getenv("STELLAR_NETWORK", "testnet")
        if self.network == "mainnet":
            self.server = Server("https://horizon.stellar.org")
            self.network_passphrase = Network.PUBLIC_NETWORK_PASSPHRASE
        else:
            self.server = Server("https://horizon-testnet.stellar.org")
            self.network_passphrase = Network.TESTNET_NETWORK_PASSPHRASE

        # Issuer keypair (loaded from env)
        issuer_secret = os.getenv("ISSUER_SECRET_KEY")
        self.issuer_keypair = Keypair.from_secret(issuer_secret) if issuer_secret else None

        # Define QOIN asset
        if self.issuer_keypair:
            self.qoin_asset = Asset("QOIN", self.issuer_keypair.public_key)

    def create_keypair(self) -> Dict[str, str]:
        '''Generate new Stellar keypair'''
        keypair = Keypair.random()
        return {
            "public_key": keypair.public_key,
            "secret_key": keypair.secret
        }

    async def fund_testnet_account(self, public_key: str):
        '''Fund account on testnet using Friendbot'''
        if self.network == "testnet":
            import requests
            response = requests.get(f"https://friendbot.stellar.org?addr={public_key}")
            return response.json()
        return None

    async def establish_trustline(self, user_secret: str):
        '''Establish trustline to QOIN asset'''
        try:
            user_keypair = Keypair.from_secret(user_secret)
            account = self.server.load_account(user_keypair.public_key)

            transaction = (
                TransactionBuilder(
                    source_account=account,
                    network_passphrase=self.network_passphrase,
                    base_fee=100
                )
                .append_change_trust_op(asset=self.qoin_asset)
                .set_timeout(30)
                .build()
            )

            transaction.sign(user_keypair)
            response = self.server.submit_transaction(transaction)
            return response['hash']
        except Exception as e:
            print(f"Trustline error: {e}")
            raise

    async def mint_tokens(self, destination: str, amount: float) -> str:
        '''Mint new QOIN tokens (issuer sends to user)'''
        try:
            # Load issuer account
            issuer_account = self.server.load_account(self.issuer_keypair.public_key)

            # Build payment transaction
            transaction = (
                TransactionBuilder(
                    source_account=issuer_account,
                    network_passphrase=self.network_passphrase,
                    base_fee=100
                )
                .append_payment_op(
                    destination=destination,
                    asset=self.qoin_asset,
                    amount=str(amount)
                )
                .set_timeout(30)
                .build()
            )

            transaction.sign(self.issuer_keypair)
            response = self.server.submit_transaction(transaction)
            return response['hash']
        except Exception as e:
            print(f"Minting error: {e}")
            raise

    async def send_payment(self, from_secret: str, to_address: str, amount: float) -> str:
        '''Send QOIN payment between users'''
        try:
            sender_keypair = Keypair.from_secret(from_secret)
            sender_account = self.server.load_account(sender_keypair.public_key)

            transaction = (
                TransactionBuilder(
                    source_account=sender_account,
                    network_passphrase=self.network_passphrase,
                    base_fee=100
                )
                .append_payment_op(
                    destination=to_address,
                    asset=self.qoin_asset,
                    amount=str(amount)
                )
                .set_timeout(30)
                .build()
            )

            transaction.sign(sender_keypair)
            response = self.server.submit_transaction(transaction)
            return response['hash']
        except Exception as e:
            print(f"Payment error: {e}")
            raise

    async def burn_tokens(self, from_secret: str, amount: float) -> str:
        '''Burn tokens by sending back to issuer'''
        try:
            user_keypair = Keypair.from_secret(from_secret)
            user_account = self.server.load_account(user_keypair.public_key)

            # Send tokens back to issuer (burns them)
            transaction = (
                TransactionBuilder(
                    source_account=user_account,
                    network_passphrase=self.network_passphrase,
                    base_fee=100
                )
                .append_payment_op(
                    destination=self.issuer_keypair.public_key,
                    asset=self.qoin_asset,
                    amount=str(amount)
                )
                .set_timeout(30)
                .build()
            )

            transaction.sign(user_keypair)
            response = self.server.submit_transaction(transaction)
            return response['hash']
        except Exception as e:
            print(f"Burning error: {e}")
            raise

    async def get_balance(self, public_key: str) -> float:
        '''Get QOIN balance for an address'''
        try:
            account = self.server.accounts().account_id(public_key).call()
            for balance in account['balances']:
                if balance['asset_type'] != 'native' and balance.get('asset_code') == 'QOIN':
                    return float(balance['balance'])
            return 0.0
        except NotFoundError:
            return 0.0
        except Exception as e:
            print(f"Balance error: {e}")
            return 0.0
