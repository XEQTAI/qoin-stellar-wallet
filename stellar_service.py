import os
from stellar_sdk import (
    Server, Keypair, TransactionBuilder, Network, Asset
)
from stellar_sdk.exceptions import NotFoundError

QOIN_CODE = "QOIN"
QOIN_ISSUER = "GDRCM33AI6O6LVMPTN5NGKQS57VBQGAVA7J6VVSIT6PO5XFKEQLODHSO"
HORIZON_URL = "https://horizon-testnet.stellar.org"

class StellarService:
    def __init__(self):
        network = os.getenv("STELLAR_NETWORK", "testnet")
        self.server = Server(HORIZON_URL)
        self.network_passphrase = (
            Network.PUBLIC_NETWORK_PASSPHRASE
            if network == "mainnet"
            else Network.TESTNET_NETWORK_PASSPHRASE
        )
        issuer_secret = os.getenv("ISSUER_SECRET_KEY")
        self.issuer_keypair = Keypair.from_secret(issuer_secret) if issuer_secret else None
        self.qoin_asset = Asset(QOIN_CODE, QOIN_ISSUER)

    async def create_and_trust_wallet(self):
        """Create wallet, fund it, and add trustline for QOIN."""
        kp = Keypair.random()
        # 1. Fund wallet
        import requests
        r = requests.get(f"https://friendbot.stellar.org?addr={kp.public_key}")
        if r.status_code != 200:
            raise Exception("Friendbot funding failed!")
        # 2. Establish trustline
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

    async def mint_tokens(self, destination, amount):
        issuer_account = self.server.load_account(self.issuer_keypair.public_key)
        tx = (
            TransactionBuilder(issuer_account, self.network_passphrase, base_fee=100)
            .append_payment_op(destination, self.qoin_asset, str(amount))
            .set_timeout(30)
            .build()
        )
        tx.sign(self.issuer_keypair)
        return self.server.submit_transaction(tx)['hash']

    async def send_payment(self, from_secret, to_address, amount):
        sender_kp = Keypair.from_secret(from_secret)
        sender_acc = self.server.load_account(sender_kp.public_key)
        tx = (
            TransactionBuilder(sender_acc, self.network_passphrase, base_fee=100)
            .append_payment_op(to_address, self.qoin_asset, str(amount))
            .set_timeout(30)
            .build()
        )
        tx.sign(sender_kp)
        return self.server.submit_transaction(tx)['hash']

    async def burn_tokens(self, from_secret, amount):
        sender_kp = Keypair.from_secret(from_secret)
        acc = self.server.load_account(sender_kp.public_key)
        tx = (
            TransactionBuilder(acc, self.network_passphrase, base_fee=100)
            .append_payment_op(self.issuer_keypair.public_key, self.qoin_asset, str(amount))
            .set_timeout(30)
            .build()
        )
        tx.sign(sender_kp)
        return self.server.submit_transaction(tx)['hash']

    async def get_balance(self, public_key: str) -> float:
        try:
            acc = self.server.accounts().account_id(public_key).call()
            for b in acc['balances']:
                if (
                    b.get('asset_type') != 'native'
                    and b.get('asset_code') == QOIN_CODE
                    and b.get('asset_issuer') == QOIN_ISSUER
                ):
                    return float(b['balance'])
            return 0.0
        except NotFoundError:
            return 0.0
