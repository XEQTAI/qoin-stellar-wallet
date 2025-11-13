#!/usr/bin/env python3
'''
Setup script for Stellar issuer account and initial configuration
Run this once to set up your issuer account and fee wallet
'''

import sys
sys.path.append('..')

from stellar_sdk import Keypair, Server, TransactionBuilder, Network, Asset
import os
from dotenv import load_dotenv

load_dotenv()

def setup_issuer():
    '''Create issuer account and set up asset'''
    print("\n=== Qoin Issuer Setup ===\n")

    # Check network
    network = os.getenv("STELLAR_NETWORK", "testnet")
    print(f"Network: {network}\n")

    # Generate issuer keypair
    print("Generating issuer keypair...")
    issuer_keypair = Keypair.random()
    print(f"Issuer Public Key: {issuer_keypair.public_key}")
    print(f"Issuer Secret Key: {issuer_keypair.secret}")
    print("⚠️  SAVE THESE KEYS IN YOUR .env FILE!\n")

    # Generate fee wallet
    print("Generating fee wallet...")
    fee_keypair = Keypair.random()
    print(f"Fee Wallet Public Key: {fee_keypair.public_key}")
    print(f"Fee Wallet Secret Key: {fee_keypair.secret}")
    print("⚠️  SAVE THESE KEYS IN YOUR .env FILE!\n")

    if network == "testnet":
        print("Funding accounts on testnet...")
        import requests

        # Fund issuer
        r1 = requests.get(f"https://friendbot.stellar.org?addr={issuer_keypair.public_key}")
        print(f"Issuer funded: {r1.status_code == 200}")

        # Fund fee wallet
        r2 = requests.get(f"https://friendbot.stellar.org?addr={fee_keypair.public_key}")
        print(f"Fee wallet funded: {r2.status_code == 200}")

    print("\n✅ Setup complete! Add these to your .env file:")
    print(f"ISSUER_SECRET_KEY={issuer_keypair.secret}")
    print(f"FEE_WALLET_ADDRESS={fee_keypair.public_key}")
    print(f"FEE_WALLET_SECRET={fee_keypair.secret}")

    return issuer_keypair, fee_keypair

if __name__ == "__main__":
    setup_issuer()
