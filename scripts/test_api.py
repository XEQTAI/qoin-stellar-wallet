#!/usr/bin/env python3
'''
Test script for Qoin API endpoints
'''

import requests
import json
import sys

BASE_URL = "http://localhost:8000"
API_KEY = "your-api-key-here"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

def test_create_wallet():
    print("\n1. Testing wallet creation...")
    data = {
        "user_id": "test_user_001",
        "email": "test@example.com"
    }
    response = requests.post(f"{BASE_URL}/api/wallet/create", json=data, headers=headers)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(json.dumps(result, indent=2))
    return result.get("wallet_address"), result.get("secret_key")

def test_deposit(wallet_address):
    print("\n2. Testing deposit...")
    data = {
        "wallet_address": wallet_address,
        "amount": 100.0
    }
    response = requests.post(f"{BASE_URL}/api/deposit", json=data, headers=headers)
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))

def test_balance(wallet_address):
    print("\n3. Testing balance check...")
    response = requests.get(f"{BASE_URL}/api/balance/{wallet_address}")
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))

def test_health():
    print("\n0. Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))

if __name__ == "__main__":
    print("=== Qoin API Test Suite ===")

    test_health()
    wallet_address, secret_key = test_create_wallet()

    if wallet_address:
        test_deposit(wallet_address)
        test_balance(wallet_address)

    print("\n✅ Tests complete!")
