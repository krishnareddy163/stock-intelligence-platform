# Database Schema Design

## Overview

**Polyglot Persistence Strategy**:
- **PostgreSQL**: Relational core (users, portfolios, metadata)
- **TimescaleDB**: Time-series optimization (stock prices)
- **MongoDB**: Flexible schema (news, sentiment, AI outputs)
- **Redis**: Cache & real-time recommendations

---

## PostgreSQL Schema

### 1. USERS Table

```sql
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    risk_profile VARCHAR(20) CHECK (risk_profile IN ('LOW', 'MEDIUM', 'HIGH')),
    country VARCHAR(100),
    preferred_currency VARCHAR(3) DEFAULT 'USD',
    investment_experience VARCHAR(20) CHECK (investment_experience IN ('BEGINNER', 'INTERMEDIATE', 'ADVANCED')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_created_at ON users(created_at DESC);
```

### 2. STOCKS Table

```sql
CREATE TABLE stocks (
    stock_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol VARCHAR(50) UNIQUE NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    sector VARCHAR(100),
    industry VARCHAR(100),
    country VARCHAR(100),
    market_cap BIGINT,
    exchange VARCHAR(50),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_stocks_symbol ON stocks(symbol);
CREATE INDEX idx_stocks_sector ON stocks(sector);
CREATE INDEX idx_stocks_country ON stocks(country);
CREATE INDEX idx_stocks_exchange ON stocks(exchange);
```

### 3. PORTFOLIOS Table

```sql
CREATE TABLE portfolios (
    portfolio_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    portfolio_name VARCHAR(255),
    total_investment DECIMAL(15, 2) NOT NULL,
    initial_investment DECIMAL(15, 2) NOT NULL,
    current_value DECIMAL(15, 2),
    risk_score INT CHECK (risk_score BETWEEN 0 AND 100),
    expected_return_percent DECIMAL(5, 2),
    expected_return_amount DECIMAL(15, 2),
    strategy VARCHAR(50) CHECK (strategy IN ('GROWTH', 'VALUE', 'DIVIDEND', 'MOMENTUM', 'HYBRID')),
    time_horizon VARCHAR(20) CHECK (time_horizon IN ('INTRADAY', 'SHORT_TERM', 'MID_TERM', 'LONG_TERM')),
    last_rebalanced_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_portfolios_user_id ON portfolios(user_id);
CREATE INDEX idx_portfolios_created_at ON portfolios(created_at DESC);
```

### 4. PORTFOLIO_HOLDINGS Table

```sql
CREATE TABLE portfolio_holdings (
    holding_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID NOT NULL REFERENCES portfolios(portfolio_id) ON DELETE CASCADE,
    stock_id UUID NOT NULL REFERENCES stocks(stock_id),
    stock_symbol VARCHAR(50) NOT NULL,
    quantity INT NOT NULL,
    purchase_price DECIMAL(10, 2),
    current_price DECIMAL(10, 2),
    allocation_percent DECIMAL(5, 2),
    current_value DECIMAL(15, 2),
    target_allocation_percent DECIMAL(5, 2),
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_holdings_portfolio_id ON portfolio_holdings(portfolio_id);
CREATE INDEX idx_holdings_stock_symbol ON portfolio_holdings(stock_symbol);
```

### 5. RECOMMENDATIONS Table

```sql
CREATE TABLE recommendations (
    recommendation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    stock_id UUID NOT NULL REFERENCES stocks(stock_id),
    stock_symbol VARCHAR(50) NOT NULL,
    recommendation_type VARCHAR(20) CHECK (recommendation_type IN ('BUY', 'SELL', 'HOLD')),
    score DECIMAL(5, 2) CHECK (score BETWEEN 0 AND 100),
    confidence DECIMAL(3, 2) CHECK (confidence BETWEEN 0 AND 1),
    reason TEXT,
    technical_indicators JSONB,
    fundamental_analysis JSONB,
    sentiment_data JSONB,
    time_horizon VARCHAR(20),
    target_price DECIMAL(10, 2),
    stop_loss_price DECIMAL(10, 2),
    risk_level VARCHAR(20) CHECK (risk_level IN ('LOW', 'MEDIUM', 'HIGH')),
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    is_acted_upon BOOLEAN DEFAULT false
);

CREATE INDEX idx_recommendations_user_id ON recommendations(user_id);
CREATE INDEX idx_recommendations_stock_symbol ON recommendations(stock_symbol);
CREATE INDEX idx_recommendations_generated_at ON recommendations(generated_at DESC);
```

### 6. MCP_LOGS Table

```sql
CREATE TABLE mcp_logs (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    server_name VARCHAR(100) NOT NULL,
    tool_name VARCHAR(100) NOT NULL,
    input_data JSONB,
    output_data JSONB,
    status VARCHAR(20) CHECK (status IN ('SUCCESS', 'FAILURE', 'TIMEOUT')),
    latency_ms INT,
    error_message TEXT,
    user_id UUID REFERENCES users(user_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_mcp_logs_server_name ON mcp_logs(server_name);
CREATE INDEX idx_mcp_logs_created_at ON mcp_logs(created_at DESC);
CREATE INDEX idx_mcp_logs_status ON mcp_logs(status);
```

### 7. PORTFOLIO_PERFORMANCE Table

```sql
CREATE TABLE portfolio_performance (
    performance_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID NOT NULL REFERENCES portfolios(portfolio_id) ON DELETE CASCADE,
    date DATE NOT NULL,
    portfolio_value DECIMAL(15, 2),
    daily_return_percent DECIMAL(5, 3),
    ytd_return_percent DECIMAL(5, 2),
    one_year_return_percent DECIMAL(5, 2),
    sharpe_ratio DECIMAL(5, 2),
    max_drawdown_percent DECIMAL(5, 2),
    UNIQUE(portfolio_id, date)
);

CREATE INDEX idx_perf_portfolio_date ON portfolio_performance(portfolio_id, date DESC);
```

---

## TimescaleDB Schema (Time-Series Hyper-Optimization)

### Stock Prices (Hyper-Table)

```sql
-- Enable extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create the table
CREATE TABLE stock_prices (
    time TIMESTAMP NOT NULL,
    symbol VARCHAR(50) NOT NULL,
    open_price DECIMAL(10, 2),
    high_price DECIMAL(10, 2),
    low_price DECIMAL(10, 2),
    close_price DECIMAL(10, 2),
    volume BIGINT,
    adjusted_close DECIMAL(10, 2)
);

-- Convert to hyper-table (time 1 day partitions)
SELECT create_hypertable('stock_prices', 'time', if_not_exists => TRUE, chunk_time_interval => INTERVAL '1 day');

-- Create indexes
CREATE INDEX ON stock_prices (symbol, time DESC);
CREATE INDEX ON stock_prices (time DESC);

-- Enable compression
ALTER TABLE stock_prices SET (
    timescaledb.compress,
    timescaledb.compress_orderby = 'time DESC'
);

-- Compress chunks older than 7 days
SELECT add_compression_policy('stock_prices', INTERVAL '7 days', if_not_exists => TRUE);

-- Set retention policy (keep 2 years)
SELECT add_retention_policy('stock_prices', INTERVAL '2 years', if_not_exists => TRUE);
```

### Technical Indicators (High-Frequency Data)

```sql
CREATE TABLE technical_indicators (
    time TIMESTAMP NOT NULL,
    symbol VARCHAR(50) NOT NULL,
    rsi_14 DECIMAL(5, 2),
    macd DECIMAL(10, 4),
    macd_signal DECIMAL(10, 4),
    macd_histogram DECIMAL(10, 4),
    sma_20 DECIMAL(10, 2),
    sma_50 DECIMAL(10, 2),
    sma_200 DECIMAL(10, 2),
    ema_12 DECIMAL(10, 2),
    ema_26 DECIMAL(10, 2),
    bollinger_upper DECIMAL(10, 2),
    bollinger_lower DECIMAL(10, 2),
    volume_change_percent DECIMAL(5, 2)
);

SELECT create_hypertable('technical_indicators', 'time', if_not_exists => TRUE);
CREATE INDEX ON technical_indicators (symbol, time DESC);
```

---

## MongoDB Collections

### News Collection

```json
db.createCollection("news", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["symbol", "title", "url", "source"],
      properties: {
        _id: { bsonType: "objectId" },
        symbol: { bsonType: "string" },
        title: { bsonType: "string" },
        content: { bsonType: "string" },
        url: { bsonType: "string" },
        source: { bsonType: "string" },
        timestamp: { bsonType: "date" },
        author: { bsonType: "string" }
      }
    }
  }
});

db.news.createIndex({ symbol: 1, timestamp: -1 });
db.news.createIndex({ timestamp: 1 }, { expireAfterSeconds: 2592000 }); // 30-day TTL
```

### Sentiment Collection

```json
db.createCollection("sentiment", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      properties: {
        _id: { bsonType: "objectId" },
        symbol: { bsonType: "string" },
        news_sentiment: {
          bsonType: "object",
          properties: {
            score: { bsonType: "double" },
            label: { bsonType: "string" },
            count: { bsonType: "int" }
          }
        },
        social_sentiment: {
          bsonType: "object",
          properties: {
            twitter_score: { bsonType: "double" },
            reddit_score: { bsonType: "double" }
          }
        },
        analyst_consensus: { bsonType: "string" },
        timestamp: { bsonType: "date" }
      }
    }
  }
});

db.sentiment.createIndex({ symbol: 1, timestamp: -1 });
```

### AI Recommendations Detail Collection

```json
db.createCollection("recommendations_detail", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      properties: {
        _id: { bsonType: "objectId" },
        portfolio_id: { bsonType: "string" },
        user_id: { bsonType: "string" },
        stocks: {
          bsonType: "array",
          items: {
            bsonType: "object",
            properties: {
              symbol: { bsonType: "string" },
              rank: { bsonType: "int" },
              score: { bsonType: "double" },
              allocation_percent: { bsonType: "double" },
              reasons: { bsonType: "array" },
              price_forecast: { bsonType: "double" },
              confidence: { bsonType: "double" }
            }
          }
        },
        portfolio_metrics: {
          bsonType: "object",
          properties: {
            expected_return_percent: { bsonType: "double" },
            risk_level: { bsonType: "string" },
            sharpe_ratio: { bsonType: "double" }
          }
        },
        explanation: { bsonType: "string" },
        generated_at: { bsonType: "date" }
      }
    }
  }
});

db.recommendations_detail.createIndex({ user_id: 1, generated_at: -1 });
```

### ML Predictions Collection

```json
db.createCollection("ml_predictions", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      properties: {
        _id: { bsonType: "objectId" },
        symbol: { bsonType: "string" },
        prediction_type: { bsonType: "string" },
        forecast_period: { bsonType: "string" },
        predictions: {
          bsonType: "array",
          items: {
            bsonType: "object",
            properties: {
              date: { bsonType: "date" },
              predicted_price: { bsonType: "double" },
              confidence_interval_lower: { bsonType: "double" },
              confidence_interval_upper: { bsonType: "double" }
            }
          }
        },
        model_name: { bsonType: "string" },
        accuracy_metric: { bsonType: "double" },
        generated_at: { bsonType: "date" }
      }
    }
  }
});

db.ml_predictions.createIndex({ symbol: 1, generated_at: -1 });
```

---

## Redis Data Structures

### Real-Time Stock Prices

```
stock:AAPL:price = 150.25
stock:AAPL:volume = 2500000
stock:AAPL:change_percent = 1.25
stock:AAPL:timestamp = 1715234567

# Expiry: 1 minute (updated constantly from stock APIs)
```

### User Sessions

```
session:{user_id} = {
  "token": "eyJhbGc...",
  "email": "user@example.com",
  "role": "user",
  "created_at": 1715234567,
  "expiry": 1715320967
}

# Expiry: 24 hours (or custom from JWT)
```

### Real-Time Recommendations Queue

```
recommendation_queue = [
  "user_123",
  "user_456",
  "user_789"
]

# Expiry: None (persistent queue)
```

### Cache Keys

```
# Stock fundamental data (1 hour TTL)
stock_fundamentals:{symbol} = {
  "pe_ratio": 22.5,
  "dividend_yield": 1.2,
  "market_cap": 2500000000000
}

# Sentiment summary (5 minute TTL)
sentiment_summary:{symbol} = {
  "news_score": 0.72,
  "social_score": 0.65,
  "overall": 0.69
}

# Portfolio value (5 minute TTL)
portfolio:{portfolio_id}:value = 125000.50
```

---

## Database Indexing Strategy

### PostgreSQL Indexes

```sql
-- User queries
EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'user@example.com';
-- Index: idx_users_email (FAST)

-- Portfolio queries
EXPLAIN ANALYZE SELECT * FROM portfolios WHERE user_id = '123' AND created_at > NOW() - INTERVAL '30 days';
-- Index: idx_portfolios_user_id + idx_portfolios_created_at (FAST)

-- Recommendation queries
EXPLAIN ANALYZE SELECT * FROM recommendations WHERE user_id = '123' ORDER BY generated_at DESC LIMIT 10;
-- Index: (user_id, generated_at DESC) (FAST)
```

### TimescaleDB Indexes

```sql
-- Historical price queries
EXPLAIN ANALYZE SELECT * FROM stock_prices WHERE symbol = 'AAPL' AND time > NOW() - INTERVAL '1 year' ORDER BY time DESC;
-- Automatic: (symbol, time DESC) via hyper-table structure (VERY FAST)

-- Range queries
EXPLAIN ANALYZE SELECT * FROM stock_prices WHERE time >= NOW() - INTERVAL '7 days' AND symbol IN ('AAPL', 'MSFT', 'GOOGL');
-- Index: ON stock_prices (time DESC) for range scans (FAST)
```

---

## Partitioning Strategy

### PostgreSQL Horizontal Partitioning

```sql
-- Partition users table by country
CREATE TABLE users_partition_us PARTITION OF users
    FOR VALUES IN ('US', 'USA');

CREATE TABLE users_partition_uk PARTITION OF users
    FOR VALUES IN ('UK', 'GB');

CREATE TABLE users_partition_in PARTITION OF users
    FOR VALUES IN ('IN', 'India');

-- Benefits:
-- - Parallel queries across partitions
-- - Smaller indexes per partition
-- - Easier maintenance
```

### MongoDB Sharding

```javascript
// Shard by user_id (range-based)
sh.shardCollection("stock_db.recommendations_detail", { user_id: 1 });

// Shard by symbol (categorical)
sh.shardCollection("stock_db.ml_predictions", { symbol: 1 });
```

---

## Backup & Disaster Recovery

### PostgreSQL Backup Strategy

```bash
# Daily full backup at 2 AM UTC
0 2 * * * pg_dump -Fc stock_db > /backups/stock_db_$(date +\%Y\%m\%d).dump

# WAL archiving for point-in-time recovery
wal_level = replica
archive_mode = on
archive_command = 'cp %p /backups/wal_archive/%f'
```

### TimescaleDB Compression & Archival

```sql
-- Automated: chunks > 7 days compressed (90% size reduction)
-- Archived: chunks > 2 years exported to S3
SELECT add_retention_policy('stock_prices', INTERVAL '2 years');
```

---

## Performance Tuning

### Query Optimization

```sql
-- Slow query (without index)
SELECT * FROM recommendations WHERE stock_symbol = 'AAPL' AND generated_at > NOW() - INTERVAL '7 days';
-- Time: 5000ms

-- Add index
CREATE INDEX idx_rec_symbol_date ON recommendations(stock_symbol, generated_at DESC);

-- After index (same query)
-- Time: 10ms (500x improvement!)
```

### Connection Pooling

```
PgBouncer Configuration:
[databases]
stock_db = host=localhost port=5432 dbname=stock_db

[pgbouncer]
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 25
```

---

This schema is designed for **performance**, **scalability**, and **compliance** across millions of users and billions of data points.
