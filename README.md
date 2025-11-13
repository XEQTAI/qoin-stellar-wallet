# 🪙 Qoin - Stellar Token ewallet System

A deposit-backed token system built on the Stellar blockchain with 1% transaction fees and closed ecosystem token burning.

## 🎯 Features

- **Deposit-Backed Tokens**: Qoins are minted only when users deposit funds
- **1% Transaction Fee**: Automatic fee deduction on all transfers
- **Closed Ecosystem**: Tokens are burned when funds leave the system
- **Stellar Blockchain**: Fast, cheap transactions (~$0.000001 per tx)
- **RESTful API**: Easy integration with FastAPI
- **PostgreSQL Database**: Secure user wallet management via Supabase

## 📋 Architecture

```
User Deposits → Mint Qoins (1:1 ratio)
User Sends Qoins → 99% to recipient, 1% fee to fee wallet
User Withdraws → Burn Qoins, release funds
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Supabase account (free tier works!)
- Stellar testnet/mainnet account

### Installation

```bash
# Clone repository
git clone https://github.com/XEQTAI/qoin-stellar-wallet.git
cd qoin-stellar-wallet

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your keys
```

### Environment Variables

Create a `.env` file:

```env
# Stellar Configuration
STELLAR_NETWORK=testnet  # or 'mainnet'
ISSUER_SECRET_KEY=YOUR_STELLAR_SECRET_KEY
FEE_WALLET_ADDRESS=YOUR_FEE_WALLET_PUBLIC_KEY

# Supabase Configuration
SUPABASE_URL=https://YOUR_PROJECT.supabase.co
SUPABASE_KEY=YOUR_SUPABASE_ANON_KEY

# API Configuration
API_SECRET_KEY=your-random-secret-key-here
```

## 📝 API Endpoints

### Create Wallet
```bash
POST /api/wallet/create
{
  "user_id": "unique_user_identifier",
  "email": "user@example.com"
}
```

### Deposit & Mint Qoins
```bash
POST /api/deposit
{
  "wallet_address": "GABC...",
  "amount": 100.00
}
```

### Send Qoins (with 1% fee)
```bash
POST /api/send
{
  "from_address": "GABC...",
  "to_address": "GXYZ...",
  "amount": 50.00
}
```

### Withdraw & Burn Qoins
```bash
POST /api/withdraw
{
  "wallet_address": "GABC...",
  "amount": 75.00
}
```

### Check Balance
```bash
GET /api/balance/{wallet_address}
```

## 🛠 Technical Stack

- **Backend**: FastAPI (Python)
- **Blockchain**: Stellar SDK (Python)
- **Database**: Supabase (PostgreSQL)
- **Deployment**: Railway / Render (free tiers)

## 💰 Token Economics

- **Token Name**: Qoin (QOIN)
- **Issuance**: Deposit-backed (no mining)
- **Supply**: Dynamic based on deposits
- **Transaction Fee**: 1% on all sends
- **Burning Mechanism**: Automatic on withdrawal

## 🔒 Security Features

- Stellar keypairs for wallets
- Environment variable secrets
- Supabase Row Level Security (RLS)
- API key authentication
- Transaction validation

## 📊 Database Schema

```sql
wallets
- id (uuid, primary key)
- user_id (text, unique)
- email (text)
- stellar_address (text, unique)
- encrypted_secret (text)
- balance (numeric)
- created_at (timestamp)

transactions
- id (uuid, primary key)
- from_address (text)
- to_address (text)
- amount (numeric)
- fee (numeric)
- tx_hash (text)
- type (enum: deposit, send, withdraw)
- created_at (timestamp)
```

## 🚀 Deployment

### Railway (Free)
```bash
# Install Railway CLI
npm i -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

### Render (Free)
1. Connect your GitHub repo
2. Create new Web Service
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables

## 🧪 Testing

```bash
# Run tests
pytest tests/

# Test on Stellar testnet
python scripts/test_stellar.py
```

## 📖 Documentation

- [Stellar Documentation](https://developers.stellar.org/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Supabase Documentation](https://supabase.com/docs)

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

MIT License - feel free to use for your own projects!

## 🙋 Support

- GitHub Issues: [Report bugs](https://github.com/XEQTAI/qoin-stellar-wallet/issues)
- Email: erik@xeqt.co.za

## 🎯 Roadmap

- [ ] Web dashboard UI
- [ ] Mobile app (React Native)
- [ ] Multi-currency support
- [ ] Staking rewards
- [ ] DeFi integrations

---

**Built with ❤️ using Stellar, FastAPI, and Supabase**
