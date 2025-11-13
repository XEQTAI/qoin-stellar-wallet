-- Qoin Wallet Database Schema for Supabase

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Wallets table
CREATE TABLE IF NOT EXISTS wallets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT UNIQUE NOT NULL,
    email TEXT NOT NULL,
    stellar_address TEXT UNIQUE NOT NULL,
    encrypted_secret TEXT NOT NULL,
    balance NUMERIC(20, 7) DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Transactions table
CREATE TABLE IF NOT EXISTS transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    from_address TEXT NOT NULL,
    to_address TEXT NOT NULL,
    amount NUMERIC(20, 7) NOT NULL,
    fee NUMERIC(20, 7) DEFAULT 0.0,
    tx_hash TEXT UNIQUE NOT NULL,
    type TEXT CHECK (type IN ('deposit', 'send', 'withdraw')),
    status TEXT DEFAULT 'completed',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_wallets_user_id ON wallets(user_id);
CREATE INDEX IF NOT EXISTS idx_wallets_stellar_address ON wallets(stellar_address);
CREATE INDEX IF NOT EXISTS idx_transactions_from_address ON transactions(from_address);
CREATE INDEX IF NOT EXISTS idx_transactions_to_address ON transactions(to_address);
CREATE INDEX IF NOT EXISTS idx_transactions_created_at ON transactions(created_at DESC);

-- Row Level Security (RLS)
ALTER TABLE wallets ENABLE ROW LEVEL SECURITY;
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;

-- RLS Policies (adjust based on your auth setup)
CREATE POLICY "Users can view their own wallet"
    ON wallets FOR SELECT
    USING (auth.uid()::text = user_id);

CREATE POLICY "Users can view their own transactions"
    ON transactions FOR SELECT
    USING (
        auth.uid()::text IN (
            SELECT user_id FROM wallets WHERE stellar_address IN (from_address, to_address)
        )
    );

-- Service role can do everything (for API)
CREATE POLICY "Service role can manage wallets"
    ON wallets FOR ALL
    USING (auth.role() = 'service_role');

CREATE POLICY "Service role can manage transactions"
    ON transactions FOR ALL
    USING (auth.role() = 'service_role');

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to auto-update updated_at
CREATE TRIGGER update_wallets_updated_at BEFORE UPDATE ON wallets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- View for wallet statistics
CREATE OR REPLACE VIEW wallet_stats AS
SELECT
    w.stellar_address,
    w.balance AS db_balance,
    COUNT(t.id) AS total_transactions,
    SUM(CASE WHEN t.from_address = w.stellar_address THEN t.amount ELSE 0 END) AS total_sent,
    SUM(CASE WHEN t.to_address = w.stellar_address THEN t.amount ELSE 0 END) AS total_received,
    SUM(CASE WHEN t.from_address = w.stellar_address THEN t.fee ELSE 0 END) AS total_fees_paid
FROM wallets w
LEFT JOIN transactions t ON (t.from_address = w.stellar_address OR t.to_address = w.stellar_address)
GROUP BY w.stellar_address, w.balance;
