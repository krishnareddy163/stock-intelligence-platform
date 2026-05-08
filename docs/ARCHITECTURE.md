# System Architecture

## Overview

The AI Global Stock Market Intelligence Platform is built on a **MCP-centric architecture** where all external communication flows through MCP servers, ensuring modularity, scalability, and maintainability.

## Core Principles

1. **MCP-First Design**: No direct API calls from LLM → all requests route through MCP servers
2. **Microservices**: Loosely coupled services communicating via async messaging
3. **Polyglot Persistence**: Best-fit database for each data type
4. **Real-time Processing**: Kafka for event streaming and ML pipelines
5. **Explainability**: Every recommendation includes reasoning

## Architecture Layers

### 1. API Gateway Layer
**Component**: Spring Cloud Gateway

```
┌─────────────────────────────────────┐
│      API Gateway                    │
│  (Spring Cloud Gateway)             │
│  - Route incoming requests          │
│  - Load balancing                   │
│  - Rate limiting                    │
│  - Authentication/Authorization     │
└──────────┬──────────────────────────┘
           │
    ┌──────┴──────┐
    │ Microservices
    └─────────────┘
```

**Responsibilities**:
- HTTP routing to downstream services
- Request/response transformation
- JWT validation
- Rate limiting
- Monitoring/logging

### 2. MCP Client Layer
**Component**: MCP Orchestrator (within recommendation service)

```
┌─────────────────────────────────┐
│  MCP Client (Orchestrator)      │
│  - Parse user requirements      │
│  - Select appropriate MCP tools │
│  - Aggregate results            │
│  - Route to LLM                 │
└────────────┬────────────────────┘
             │
      ┌──────┴──────┐
      │ MCP Servers
      └─────────────┘
```

**Flow**:
```
User Query → API → MCP Client
↓
Determine required MCP servers (tools)
↓
Send requests in parallel (where possible)
↓
Aggregate responses
↓
Send to LLM for reasoning/ranking
↓
Generate structured output
```

### 3. MCP Servers Layer (The Brain)

#### 3.1 Stock Data Server
**Language**: Python FastAPI
**External APIs**: yfinance, Alpha Vantage, Yahoo Finance

```python
[Stock Data Server]
├── get_stock_price(symbol) → Real-time price
├── get_historical_data(symbol, timeframe) → OHLCV
├── get_market_index_data(index) → Index performance
├── get_sector_data(sector) → Sector metrics
└── get_earnings_data(symbol) → Earnings & fundamentals
```

**Data Flow**:
```
User asks: "Top 5 IT stocks in India"
↓
Stock Data Server:
- Fetch all IT sector stocks from Nifty 50
- Get current prices
- Get 1-year historical data
↓
Response → to Prediction Server & Sentiment Server
```

#### 3.2 Sentiment Server
**Language**: Python FastAPI
**Models**: HuggingFace DistilBERT, FinBERT

```python
[Sentiment Server]
├── get_news_sentiment(symbol) → News-based sentiment
├── get_social_sentiment(symbol) → Twitter/Reddit sentiment
├── get_analyst_consensus(symbol) → Analyst ratings
└── get_sentiment_trend(symbol, days) → Sentiment trajectory
```

**Integration**:
- Real-time news API (NewsAPI, Finnhub)
- Twitter/Reddit social API
- Sentiment stored in MongoDB for trend analysis

#### 3.3 Prediction Server
**Language**: Python FastAPI
**Models**: LSTM, XGBoost, PyTorch

```python
[Prediction Server]
├── predict_stock_price(symbol, days, model) → Price forecast
├── predict_market_trend(index) → Bull/Bear/Neutral
├── predict_volatility(symbol) → Volatility forecast
├── predict_crash_risk(symbol) → Risk score
└── predict_momentum(symbol) → Momentum strength
```

**ML Pipeline**:
```
Historical Data (TimescaleDB)
    ↓
Feature Engineering (Pandas)
    ↓
LSTM Model (short-term | 1-7 days)
XGBoost Model (medium-term | 7-30 days)
Prophet/ARIMA (long-term | 30+ days)
    ↓
Confidence Score + Prediction
    ↓
Response to MCP Client
```

#### 3.4 Portfolio Server
**Language**: Java Spring Boot / Python FastAPI

```python
[Portfolio Server]
├── build_portfolio(preferences, amount, risk) → Portfolio construction
├── optimize_portfolio(stocks, weights) → Markowitz optimization
├── rebalance_portfolio(current_portfolio, new_market_data) → Rebalancing
├── simulate_portfolio(stocks, weights, days) → Backtesting
└── estimate_risk_metrics(portfolio) → VaR, Sharpe, Sortino
```

**Algorithm**:
- Modern Portfolio Theory (Markowitz)
- Efficient Frontier calculation
- Risk-Return optimization
- Diversification scoring

#### 3.5 Alert Server
**Language**: Python FastAPI

```python
[Alert Server]
├── generate_buy_signals(symbol) → Buy triggers
├── generate_sell_signals(symbol) → Sell triggers
├── risk_alerts(portfolio) → Risk warnings
└── news_alerts(symbols) → News-triggered alerts
```

---

### 4. Microservices Layer

#### User Service
- User registration/authentication
- Profile management
- Risk profile assessment

#### Recommendation Service
- **MCP Client integration**
- Orchestrates all MCP servers
- Ranks and filters recommendations
- Explanation generation (XAI layer)

#### Portfolio Service
- CRUD operations on portfolios
- Portfolio history tracking
- Performance analytics

---

### 5. Data Layer

```
┌────────────────────────────────────────────────────────┐
│              POLYGLOT DATA ARCHITECTURE                 │
├────────────────────────────────────────────────────────┤
│                                                        │
│  PostgreSQL         TimescaleDB      MongoDB   Redis   │
│  ─────────          ───────────      ───────   ─────   │
│  - Users            - OHLCV Data     - News    - Cache │
│  - Portfolios       - Prices (1min)  - Sentiment- Real-│
│  - Metadata         - Technical      - AI       time   │
│                      Indicators       Output    Signals │
│                                                        │
│  EC2 + RDS          EC2 + RDS        EC2 +    EC2 +    │
│                                      Atlas    Cluster  │
│                                                        │
└────────────────────────────────────────────────────────┘
```

#### PostgreSQL (Core)
```sql
-- Users
CREATE TABLE users (
    user_id UUID PRIMARY KEY,
    email VARCHAR UNIQUE,
    risk_profile VARCHAR,
    created_at TIMESTAMP
);

-- Portfolios
CREATE TABLE portfolios (
    portfolio_id UUID PRIMARY KEY,
    user_id UUID REFERENCES users,
    total_investment DECIMAL,
    created_at TIMESTAMP
);

-- Recommendations Log
CREATE TABLE recommendations (
    recommendation_id UUID PRIMARY KEY,
    user_id UUID,
    stock_symbol VARCHAR,
    score DECIMAL,
    reason TEXT,
    created_at TIMESTAMP
);
```

#### TimescaleDB (Time-Series)
```sql
-- Hyper-optimized for stock prices
CREATE TABLE stock_prices (
    time TIMESTAMP,
    symbol VARCHAR,
    price_open DECIMAL,
    price_high DECIMAL,
    price_low DECIMAL,
    price_close DECIMAL,
    volume BIGINT,
    PRIMARY KEY (time, symbol)
) WITH (timescaledb.compress=true);

CREATE INDEX ON stock_prices (symbol, time DESC);
```

#### MongoDB (Flexible Schema)
```json
// News & Sentiment
db.news.insertOne({
    _id: ObjectId(),
    symbol: "AAPL",
    title: "Apple announces...",
    sentiment: "positive",
    score: 0.85,
    timestamp: ISODate(),
    source: "Reuters"
});

// AI Recommendations (with explanations)
db.recommendations_detail.insertOne({
    _id: ObjectId(),
    portfolio_id: UUID(),
    stocks: [
        {
            symbol: "NVDA",
            rank: 1,
            score: 92.5,
            reasons: [
                "Strong technical momentum",
                "Positive sentiment (0.82)",
                "ML prediction: +15% in 30d"
            ]
        }
    ]
});
```

#### Redis (Cache & Real-Time)
```
// Cache stock prices
stock:AAPL:price → 150.25 (expires 1 min)

// Real-time recommendation queue
recommendation_queue → [user_1, user_5, user_23]

// Active user sessions
session:{user_id} → {token, expiry}
```

---

### 6. Real-Time Processing Layer

**Apache Kafka Pipelines**:

```
Stock Price Updates
    ↓
kafka-topic: stock-prices
    ↓
Kafka Consumers:
  ├── TimescaleDB Writer
  ├── Redis Cache Updater
  ├── Alert Trigger (if price hits thresholds)
  └── Prediction Model Feeder
```

**Streaming Architecture**:
```
┌──────────────────────────────────────┐
│  Data Sources                        │
│  - Stock APIs (yfinance)             │
│  - News APIs (NewsAPI)               │
│  - Social Data (Twitter)             │
└──────────────┬───────────────────────┘
               │
        ┌──────▼──────┐
        │ Apache Kafka │
        └──────┬──────┘
               │
        ┌──────┴──────┬──────────┬──────────┐
        │             │          │          │
    ┌───▼──┐   ┌──────▼──┐  ┌───▼────┐  ┌─▼────┐
    │Redis │   │TimescaleDB   │MongoDB│  │Alert │
    │Cache │   │             │       │  │Queue │
    └──────┘   └──────────┘  └───────┘  └──────┘
```

---

### 7. MCP → LLM → Output Flow (CRITICAL)

```
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: User Query Arrives at API                           │
│ Input: "I have $10k, medium risk, 1-year horizon, IT sector"│
└────────────────┬────────────────────────────────────────────┘

┌────────────────▼────────────────────────────────────────────┐
│ STEP 2: MCP Client Analyzes Query                           │
│ - Extract constraints (amount, risk, horizon, sector)       │
│ - Determine required MCP tools                              │
│ - Create execution plan                                     │
└────────────────┬────────────────────────────────────────────┘

┌────────────────▼────────────────────────────────────────────┐
│ STEP 3: Parallel MCP Server Calls                           │
│                                                             │
│ Call 1: Stock Data Server                                   │
│   → get_market_index_data("Nifty IT")                       │
│   → Returns: ~40 IT companies                               │
│                                                             │
│ Call 2: Sentiment Server                                    │
│   → get_news_sentiment([symbols])                           │
│   → Returns: Sentiment scores (-1.0 to +1.0)               │
│                                                             │
│ Call 3: Prediction Server                                   │
│   → predict_stock_price([symbols], 365 days)               │
│   → Returns: Price forecasts with confidence               │
│                                                             │
│ Call 4: Fundamentals                                        │
│   → get_pe_ratio, earnings_growth, etc.                    │
│                                                             │
│ Timeout: 5 seconds (fail gracefully if one server slow)    │
└────────────────┬────────────────────────────────────────────┘

┌────────────────▼────────────────────────────────────────────┐
│ STEP 4: Aggregate & Prepare for LLM                         │
│                                                             │
│ Data Format (JSON):                                         │
│ {                                                           │
│   "stocks": [                                               │
│     {                                                       │
│       "symbol": "INFOSYS",                                  │
│       "price_current": 1850.00,                             │
│       "price_forecast_1y": 2150.00,                         │
│       "price_growth_percent": 16.2,                         │
│       "sentiment_score": 0.72,                              │
│       "pe_ratio": 22.5,                                     │
│       "earnings_growth_yoy": 14.2,                          │
│       "prediction_confidence": 0.78,                        │
│       "volatility": 18.5,                                   │
│       "analyst_rating": "BUY"                               │
│     },                                                      │
│     ... (more stocks)                                       │
│   ]                                                         │
│ }                                                           │
└────────────────┬────────────────────────────────────────────┘

┌────────────────▼────────────────────────────────────────────┐
│ STEP 5: LLM Reasoning & Ranking                             │
│                                                             │
│ Prompt to LLM:                                              │
│ "Given $10k, medium risk, 1-year horizon, IT sector:"      │
│  1. Rank stocks by risk-adjusted returns                    │
│  2. Build diversified portfolio (3-5 stocks)               │
│  3. Calculate allocation percentages                        │
│  4. Explain each selection (why, risks, upsides)           │
│  5. Provide confidence score                                │
│                                                             │
│ LLM Output:                                                 │
│ {                                                           │
│   "portfolio": [                                            │
│     {"symbol": "INFOSYS", "allocation": 35%, "reason": "..."}│
│     {"symbol": "TCS", "allocation": 30%, "reason": "..."}   │
│     {"symbol": "WIPRO", "allocation": 20%, "reason": "..."} │
│     {"symbol": "HCL", "allocation": 15%, "reason": "..."}   │
│   ],                                                        │
│   "expected_return": "14-18% annually",                     │
│   "risk_level": "Medium",                                   │
│   "confidence": 0.82,                                       │
│   "key_risks": ["..."],                                     │
│   "rebalance_trigger": "quarterly"                          │
│ }                                                           │
└────────────────┬────────────────────────────────────────────┘

┌────────────────▼────────────────────────────────────────────┐
│ STEP 6: Portfolio Service Saves & Returns                   │
│                                                             │
│ Save to PostgreSQL:                                         │
│ - Portfolio record                                          │
│ - Holdings (stocks + allocation)                            │
│ - Recommendation metadata                                   │
│                                                             │
│ Return to Frontend:                                         │
│ - JSON with full details                                    │
│ - Charts/visualizations ready                               │
│ - Risk metrics calculated                                   │
└─────────────────────────────────────────────────────────────┘
```

---

## Scalability Strategy

### Horizontal Scaling

**MCP Servers**:
```
Load Balancer (AWS ELB)
    ↓
├─ Stock Data Server (5 replicas)
├─ Sentiment Server (3 replicas)
├─ Prediction Server (10 replicas) ← CPU intensive
├─ Portfolio Server (2 replicas)
└─ Alert Server (2 replicas)
```

**Backend Services**:
```
API Gateway (Primary)
  ├─ User Service (2 replicas)
  ├─ Recommendation Service (5 replicas)
  └─ Portfolio Service (3 replicas)
```

### Data Scaling

**Sharding Strategy** (millions of users):
```
PostgreSQL:
  - Shard by user_id % 10 (10 database nodes)
  - Each node handles 10M users

TimescaleDB:
  - Hyper-tables compressed (auto)
  - Retention: keep 2 years, archive beyond
  - Parallel queries on multiple chunks
```

### Caching Strategy

```
L1 Cache (Redis):
  - Stock prices (1 min TTL)
  - Sentiment scores (5 min TTL)
  - User sessions (active duration)

L2 Cache (Browser):
  - Historical charts (1 hour)
  - Portfolio data (5 min)

L3 Cache (CDN):
  - Static assets
  - Reference data (sectors, indices)
```

---

## Fault Tolerance & Resilience

### Circuit Breaker Pattern

```python
@circuit_breaker(failure_threshold=5, timeout=60)
def call_external_api():
    """Fails gracefully if external API down"""
    pass
```

### Retry Mechanism

```yaml
MCP Server Calls:
  initial_timeout: 2s
  retry_count: 3
  backoff_strategy: exponential
  fallback:
    - Use cached data if available
    - Return partial results
    - Graceful degradation
```

### Dead Letter Queue (DLQ)

```
Failed Kafka Messages
    ↓
DLQ Topic
    ↓
Retry Worker (exponential backoff)
    ↓
Success: back to main topic
Failure: alert + human review
```

---

## Security Model

### Authentication & Authorization

```
┌─────────────────────────────────┐
│  User                            │
└────────────┬────────────────────┘
             │
        ┌────▼─────┐
        │ OAuth2   │
        │ Provider │
        └────┬─────┘
             │
        ┌────▼──────────────────┐
        │ API Gateway           │
        │ - Validate JWT        │
        │ - Extract claims      │
        │ - Authorize endpoint  │
        └────┬─────────────────┘
             │
        ┌────▼───────────┐
        │ Microservice   │
        └────────────────┘
```

### MCP Server Isolation

- Each MCP server runs in isolated container
- Network policies restrict inter-server communication
- Service-to-service mTLS (mutual TLS)

### Data Encryption

```
In Transit:
  - TLS 1.3 for all APIs
  - mTLS between services

At Rest:
  - PostgreSQL: encryption-at-rest with AWS KMS
  - MongoDB: field-level encryption
  - Sensitive data (API keys): HSM-backed Vault
```

---

## Monitoring & Observability

### Prometheus Metrics

```
- mcp_request_duration_ms
- mcp_request_errors_total
- stockdata_api_latency_ms
- ml_prediction_inference_time_ms
- portfolio_optimization_time_ms
- kafka_consumer_lag_ms
```

### Distributed Tracing

```
Jaeger / AWS X-Ray:
- Trace ID: correlates all services
- Span per MCP server call
- Latency breakdown per component
```

### Logging

```
ELK Stack:
- Elasticsearch: indexed logs
- Logstash: log aggregation
- Kibana: visualization
- Alerts: on error patterns
```

---

This architecture is designed for **production scale**, **fault tolerance**, **explainability**, and **modular extensibility**.
