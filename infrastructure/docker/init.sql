-- ============================================================
-- Stock Intelligence Platform — PostgreSQL Init Script
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ──────────────────────────────────────────────
-- USERS
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    user_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email            VARCHAR(255) UNIQUE NOT NULL,
    name             VARCHAR(255) NOT NULL,
    password_hash    VARCHAR(255) NOT NULL,
    risk_profile     VARCHAR(20)  CHECK (risk_profile IN ('LOW', 'MEDIUM', 'HIGH')) DEFAULT 'MEDIUM',
    country          VARCHAR(100),
    preferred_currency VARCHAR(3) DEFAULT 'USD',
    investment_experience VARCHAR(20) CHECK (investment_experience IN ('BEGINNER', 'INTERMEDIATE', 'ADVANCED')) DEFAULT 'BEGINNER',
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active        BOOLEAN DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_users_email       ON users (email);
CREATE INDEX IF NOT EXISTS idx_users_country     ON users (country);
CREATE INDEX IF NOT EXISTS idx_users_created_at  ON users (created_at DESC);

-- ──────────────────────────────────────────────
-- STOCKS
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS stocks (
    stock_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol        VARCHAR(50) UNIQUE NOT NULL,
    company_name  VARCHAR(255) NOT NULL,
    sector        VARCHAR(100),
    industry      VARCHAR(100),
    country       VARCHAR(100),
    market_cap    BIGINT,
    exchange      VARCHAR(50),
    is_active     BOOLEAN DEFAULT TRUE,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_stocks_symbol   ON stocks (symbol);
CREATE INDEX IF NOT EXISTS idx_stocks_sector   ON stocks (sector);
CREATE INDEX IF NOT EXISTS idx_stocks_country  ON stocks (country);
CREATE INDEX IF NOT EXISTS idx_stocks_exchange ON stocks (exchange);

-- ──────────────────────────────────────────────
-- PORTFOLIOS
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS portfolios (
    portfolio_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id              UUID NOT NULL REFERENCES users (user_id) ON DELETE CASCADE,
    portfolio_name       VARCHAR(255),
    total_investment     DECIMAL(15, 2) NOT NULL,
    initial_investment   DECIMAL(15, 2) NOT NULL,
    current_value        DECIMAL(15, 2),
    risk_score           INT CHECK (risk_score BETWEEN 0 AND 100),
    expected_return_percent DECIMAL(5, 2),
    strategy             VARCHAR(50) CHECK (strategy IN ('GROWTH','VALUE','DIVIDEND','MOMENTUM','HYBRID')),
    time_horizon         VARCHAR(20) CHECK (time_horizon IN ('INTRADAY','SHORT_TERM','MID_TERM','LONG_TERM')),
    last_rebalanced_at   TIMESTAMP,
    created_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_portfolios_user_id    ON portfolios (user_id);
CREATE INDEX IF NOT EXISTS idx_portfolios_created_at ON portfolios (created_at DESC);

-- ──────────────────────────────────────────────
-- PORTFOLIO HOLDINGS
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS portfolio_holdings (
    holding_id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id            UUID NOT NULL REFERENCES portfolios (portfolio_id) ON DELETE CASCADE,
    stock_symbol            VARCHAR(50) NOT NULL,
    quantity                INT NOT NULL CHECK (quantity > 0),
    purchase_price          DECIMAL(10, 2),
    current_price           DECIMAL(10, 2),
    allocation_percent      DECIMAL(5, 2),
    current_value           DECIMAL(15, 2),
    target_allocation_percent DECIMAL(5, 2),
    added_at                TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_holdings_portfolio_id  ON portfolio_holdings (portfolio_id);
CREATE INDEX IF NOT EXISTS idx_holdings_stock_symbol  ON portfolio_holdings (stock_symbol);

-- ──────────────────────────────────────────────
-- RECOMMENDATIONS
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS recommendations (
    recommendation_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL REFERENCES users (user_id) ON DELETE CASCADE,
    stock_symbol        VARCHAR(50) NOT NULL,
    recommendation_type VARCHAR(20) CHECK (recommendation_type IN ('BUY','SELL','HOLD')),
    score               DECIMAL(5, 2) CHECK (score BETWEEN 0 AND 100),
    confidence          DECIMAL(3, 2) CHECK (confidence BETWEEN 0 AND 1),
    reason              TEXT,
    technical_indicators JSONB,
    fundamental_analysis JSONB,
    sentiment_data      JSONB,
    time_horizon        VARCHAR(20),
    target_price        DECIMAL(10, 2),
    stop_loss_price     DECIMAL(10, 2),
    risk_level          VARCHAR(20) CHECK (risk_level IN ('LOW','MEDIUM','HIGH')),
    generated_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at          TIMESTAMP,
    is_acted_upon       BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_rec_user_id        ON recommendations (user_id);
CREATE INDEX IF NOT EXISTS idx_rec_stock_symbol   ON recommendations (stock_symbol);
CREATE INDEX IF NOT EXISTS idx_rec_generated_at   ON recommendations (generated_at DESC);
CREATE INDEX IF NOT EXISTS idx_rec_symbol_date    ON recommendations (stock_symbol, generated_at DESC);

-- ──────────────────────────────────────────────
-- MCP LOGS
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS mcp_logs (
    log_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    server_name   VARCHAR(100) NOT NULL,
    tool_name     VARCHAR(100) NOT NULL,
    input_data    JSONB,
    output_data   JSONB,
    status        VARCHAR(20) CHECK (status IN ('SUCCESS','FAILURE','TIMEOUT')),
    latency_ms    INT,
    error_message TEXT,
    user_id       UUID REFERENCES users (user_id),
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_mcp_server_name ON mcp_logs (server_name);
CREATE INDEX IF NOT EXISTS idx_mcp_created_at  ON mcp_logs (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_mcp_status      ON mcp_logs (status);

-- ──────────────────────────────────────────────
-- PORTFOLIO PERFORMANCE
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS portfolio_performance (
    performance_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id            UUID NOT NULL REFERENCES portfolios (portfolio_id) ON DELETE CASCADE,
    date                    DATE NOT NULL,
    portfolio_value         DECIMAL(15, 2),
    daily_return_percent    DECIMAL(5, 3),
    ytd_return_percent      DECIMAL(5, 2),
    one_year_return_percent DECIMAL(5, 2),
    sharpe_ratio            DECIMAL(5, 2),
    max_drawdown_percent    DECIMAL(5, 2),
    UNIQUE (portfolio_id, date)
);

CREATE INDEX IF NOT EXISTS idx_perf_portfolio_date ON portfolio_performance (portfolio_id, date DESC);

-- ──────────────────────────────────────────────
-- SEED DATA
-- ──────────────────────────────────────────────
INSERT INTO stocks (symbol, company_name, sector, industry, country, exchange) VALUES
    ('AAPL',   'Apple Inc.',             'Technology',   'Consumer Electronics', 'US', 'NASDAQ'),
    ('MSFT',   'Microsoft Corp.',        'Technology',   'Software',             'US', 'NASDAQ'),
    ('GOOGL',  'Alphabet Inc.',          'Technology',   'Internet Services',    'US', 'NASDAQ'),
    ('AMZN',   'Amazon.com Inc.',        'Consumer',     'E-Commerce',           'US', 'NASDAQ'),
    ('NVDA',   'NVIDIA Corp.',           'Technology',   'Semiconductors',       'US', 'NASDAQ'),
    ('META',   'Meta Platforms',         'Technology',   'Social Media',         'US', 'NASDAQ'),
    ('TSLA',   'Tesla Inc.',             'Automotive',   'EV Manufacturer',      'US', 'NASDAQ'),
    ('JPM',    'JPMorgan Chase',         'Finance',      'Banking',              'US', 'NYSE'),
    ('JNJ',    'Johnson & Johnson',      'Healthcare',   'Pharmaceuticals',      'US', 'NYSE'),
    ('V',      'Visa Inc.',              'Finance',      'Payments',             'US', 'NYSE'),
    ('RELIANCE.NS', 'Reliance Industries', 'Energy',     'Conglomerate',         'IN', 'NSE'),
    ('TCS.NS',      'Tata Consultancy',   'Technology',  'IT Services',          'IN', 'NSE'),
    ('INFY.NS',     'Infosys Ltd.',       'Technology',  'IT Services',          'IN', 'NSE'),
    ('HDFCBANK.NS', 'HDFC Bank',          'Finance',     'Banking',              'IN', 'NSE'),
    ('ICICIBANK.NS','ICICI Bank',         'Finance',     'Banking',              'IN', 'NSE')
ON CONFLICT (symbol) DO NOTHING;

-- ──────────────────────────────────────────────
-- TimescaleDB (applied separately if extension available)
-- ──────────────────────────────────────────────
-- Run these commands against the timeseries_db database:
--
-- CREATE EXTENSION IF NOT EXISTS timescaledb;
--
-- CREATE TABLE IF NOT EXISTS stock_prices (
--     time          TIMESTAMP NOT NULL,
--     symbol        VARCHAR(50) NOT NULL,
--     open_price    DECIMAL(10, 2),
--     high_price    DECIMAL(10, 2),
--     low_price     DECIMAL(10, 2),
--     close_price   DECIMAL(10, 2),
--     volume        BIGINT,
--     adjusted_close DECIMAL(10, 2)
-- );
-- SELECT create_hypertable('stock_prices', 'time', if_not_exists => TRUE, chunk_time_interval => INTERVAL '1 day');
-- CREATE INDEX ON stock_prices (symbol, time DESC);
-- ALTER TABLE stock_prices SET (timescaledb.compress, timescaledb.compress_orderby = 'time DESC');
-- SELECT add_compression_policy('stock_prices', INTERVAL '7 days', if_not_exists => TRUE);
-- SELECT add_retention_policy('stock_prices', INTERVAL '2 years', if_not_exists => TRUE);
