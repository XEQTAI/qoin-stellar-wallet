from stellar_sdk import Server, Keypair, TransactionBuilder, Network, Asset, Account
from stellar_sdk.exceptions import NotFoundError, BadRequestError
import os
from typing import Dict

# --- QOIN Settings --
QOIN_CODE = "QOIN"
QOIN_ISSUER = "GDRCM33AI6O6LVMPTN5NGKQS57VBQGAVA7J6VVSIT6PO5XFKEQLODHSO"  # Your QOIN issuer public key (keep secret key safe!)

HORIZON_URL = "https://horizon-testnet.stellar.org"


class StellarService:
    def __init__(self):
        self.network = os.getenv("STELLAR_NETWORK", "testnet")
        if self.network == "mainnet":
            self.server = Server("https://horizon.stellar.org")
            self.network_passphrase = Network.PUBLIC_NETWORK_PASSPHRASE
        else:
            self.server = Server(HORIZON_URL)
            self.network_passphrase = Network.TESTNET_NETWORK_PASSPHRASE

        issuer_secret = os.getenv("ISSUER_SECRET_KEY")
        self.issuer_keypair = Keypair.from_secret(issuer_secret) if issuer_secret else None
        self.qoin_asset = Asset(QOIN_CODE, QOIN_ISSUER)

    async def create_and_trust_wallet(self) -> Dict[str, str]:
        '''Creates new Stellar wallet, funds it (testnet), and establishes QOIN trustline'''
        keypair = Keypair.random()

        # 1. Fund with Friendbot for testnet
        if self.network == "testnet":
            import requests
            resp = requests.get(f"https://friendbot.stellar.org?addr={keypair.public_key}")
            if resp.status_code != 200:
                raise Exception("Friendbot funding failed!")

        # 2. Establish trustline for QOIN asset
        account = self.server.load_account(keypair.public_key)
        tx = (
            TransactionBuilder(
                source_account=account,
                network_passphrase=self.network_passphrase,
                base_fee=100)
            .append_change_trust_op(asset=self.qoin_asset)
            .set_timeout(30)
            .build()
        )
        tx.sign(keypair)
        self.server.submit_transaction(tx)

        return {
            "public_key": keypair.public_key,
            "secret_key": keypair.secret
        }

    async def mint_tokens(self, destination: str, amount: float) -> str:
        '''Mint new QOIN tokens (issuer sends to user)'''
        try:
            issuer_account = self.server.load_account(self.issuer_keypair.public_key)
            tx = (
                TransactionBuilder(
                    source_account=issuer_account,
                    network_passphrase=self.network_passphrase,
                    base_fee=100)
                .append_payment_op(
                    destination=destination,
                    asset=self.qoin_asset,
                    amount=str(amount)
                )
                .set_timeout(30)
                .build()
            )
            tx.sign(self.issuer_keypair)
            response = self.server.submit_transaction(tx)
            return response['hash']
        except Exception as e:
            print(f"Minting error: {e}")
            raise

    async def send_payment(self, from_secret: str, to_address: str, amount: float) -> str:
        '''Send QOIN payment between users'''
        try:
            sender_kp = Keypair.from_secret(from_secret)
            sender_account = self.server.load_account(sender_kp.public_key)
            tx = (
                TransactionBuilder(
                    source_account=sender_account,
                    network_passphrase=self.network_passphrase,
                    base_fee=100)
                .append_payment_op(
                    destination=to_address,
                    asset=self.qoin_asset,
                    amount=str(amount)
                )
                .set_timeout(30)
                .build()
            )
            tx.sign(sender_kp)
            response = self.server.submit_transaction(tx)
            return response['hash']
        except Exception as e:
            print(f"Payment error: {e}")
            raise

    async def burn_tokens(self, from_secret: str, amount: float) -> str:
        '''Burn tokens by sending back to issuer'''
        try:
            user_kp = Keypair.from_secret(from_secret)
            user_account = self.server.load_account(user_kp.public_key)
            tx = (
                TransactionBuilder(
                    source_account=user_account,
                    network_passphrase=self.network_passphrase,
                    base_fee=100)
                .append_payment_op(
                    destination=self.issuer_keypair.public_key,
                    asset=self.qoin_asset,
                    amount=str(amount)
                )
                .set_timeout(30)
                .build()
            )
            tx.sign(user_kp)
            response = self.server.submit_transaction(tx)
            return response['hash']
        except Exception as e:
            print(f"Burning error: {e}")
            raise

    async def get_balance(self, public_key: str) -> float:
        '''Get QOIN balance for an address'''
        try:
            account = self.server.accounts().account_id(public_key).call()
            for balance in account['balances']:
                if balance['asset_type'] != 'native' and balance.get('asset_code') == QOIN_CODE and balance.get('asset_issuer') == QOIN_ISSUER:
                    return float(balance['balance'])
            return 0.0
        except NotFoundError:
            return 0.0
        except Exception as e:
            print(f"Balance error: {e}")
            return 0.0
