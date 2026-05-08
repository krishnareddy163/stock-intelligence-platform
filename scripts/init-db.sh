#!/bin/bash

# Initialize PostgreSQL Schema
# Run this script after PostgreSQL is up

echo "Initializing PostgreSQL schema..."

# Connection parameters
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5432}
DB_NAME=${DB_NAME:-stock_db}
DB_USER=${DB_USER:-stock_user}

# Create schema
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME << 'EOF'

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS uuid-ossp;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- USERS Table
CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    risk_profile VARCHAR(20) CHECK (risk_profile IN ('LOW', 'MEDIUM', 'HIGH')),
    country VARCHAR(100),
    preferred_currency VARCHAR(3) DEFAULT 'USD',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_created_at ON users(created_at DESC);

-- STOCKS Table
CREATE TABLE IF NOT EXISTS stocks (
    stock_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol VARCHAR(50) UNIQUE NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    sector VARCHAR(100),
    industry VARCHAR(100),
    country VARCHAR(100),
    market_cap BIGINT,
    exchange VARCHAR(50),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_stocks_symbol ON stocks(symbol);
CREATE INDEX idx_stocks_sector ON stocks(sector);

-- PORTFOLIOS Table
CREATE TABLE IF NOT EXISTS portfolios (
    portfolio_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    portfolio_name VARCHAR(255),
    total_investment DECIMAL(15, 2) NOT NULL,
    current_value DECIMAL(15, 2),
    risk_score INT CHECK (risk_score BETWEEN 0 AND 100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_portfolios_user_id ON portfolios(user_id);

-- PORTFOLIO_HOLDINGS Table
CREATE TABLE IF NOT EXISTS portfolio_holdings (
    holding_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID NOT NULL REFERENCES portfolios(portfolio_id) ON DELETE CASCADE,
    stock_id UUID NOT NULL REFERENCES stocks(stock_id),
    stock_symbol VARCHAR(50) NOT NULL,
    quantity INT NOT NULL,
    purchase_price DECIMAL(10, 2),
    allocation_percent DECIMAL(5, 2),
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_holdings_portfolio_id ON portfolio_holdings(portfolio_id);

-- RECOMMENDATIONS Table
CREATE TABLE IF NOT EXISTS recommendations (
    recommendation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    stock_id UUID NOT NULL REFERENCES stocks(stock_id),
    stock_symbol VARCHAR(50) NOT NULL,
    recommendation_type VARCHAR(20) CHECK (recommendation_type IN ('BUY', 'SELL', 'HOLD')),
    score DECIMAL(5, 2),
    confidence DECIMAL(3, 2),
    reason TEXT,
    target_price DECIMAL(10, 2),
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

CREATE INDEX idx_recommendations_user_id ON recommendations(user_id);
CREATE INDEX idx_recommendations_generated_at ON recommendations(generated_at DESC);

-- MCP_LOGS Table
CREATE TABLE IF NOT EXISTS mcp_logs (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    server_name VARCHAR(100) NOT NULL,
    tool_name VARCHAR(100) NOT NULL,
    status VARCHAR(20) CHECK (status IN ('SUCCESS', 'FAILURE', 'TIMEOUT')),
    latency_ms INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_mcp_logs_created_at ON mcp_logs(created_at DESC);

-- Sample data: Popular stocks
INSERT INTO stocks (symbol, company_name, sector, country, exchange) VALUES
    ('INFY', 'Infosys Limited', 'IT', 'IN', 'NSE'),
    ('TCS', 'Tata Consultancy Services', 'IT', 'IN', 'NSE'),
    ('WIPRO', 'Wipro Limited', 'IT', 'IN', 'NSE'),
    ('AAPL', 'Apple Inc.', 'Technology', 'US', 'NASDAQ'),
    ('MSFT', 'Microsoft Corporation', 'Technology', 'US', 'NASDAQ'),
    ('GOOGL', 'Alphabet Inc.', 'Technology', 'US', 'NASDAQ'),
    ('AMZN', 'Amazon.com Inc.', 'Consumer', 'US', 'NASDAQ'),
    ('TSLA', 'Tesla Inc.', 'Automotive', 'US', 'NASDAQ')
ON CONFLICT (symbol) DO NOTHING;

-- Create admin user (password: admin123)
INSERT INTO users (email, name, password_hash, risk_profile, country)
    VALUES ('admin@stockintel.com', 'Administrator', '$2b$12$...', 'HIGH', 'US')
ON CONFLICT (email) DO NOTHING;

EOF

echo "✅ PostgreSQL schema initialized"
