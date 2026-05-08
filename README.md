# AI Global Stock Market Intelligence Platform

A production-grade, MCP-powered AI platform providing stock recommendations, portfolio optimization, and predictive market intelligence across global markets.

## 🎯 Project Overview

This system combines:
- **Bloomberg Terminal** — financial data & analytics
- **TradingView** — interactive charts
- **Hedge Fund Quant System** — AI predictions & rankings
- **Financial Advisor** — chat interface with explainable AI
- **MCP Architecture** — modular, extensible plugin ecosystem

## 🏗️ Architecture

### High-Level Flow
```
User Input
    ↓
API Gateway (Spring Cloud Gateway)
    ↓
MCP Client (Orchestration Layer)
    ↓
MCP Servers (Stock Data, Sentiment, ML Prediction, Portfolio, Alerts)
    ↓
External APIs / ML Models / Databases
    ↓
AI Reasoning Layer (LLM)
    ↓
Structured Output → Dashboard → User
```

## 📁 Project Structure

```
claude_mcp_project/
├── README.md
├── ARCHITECTURE.md
├── docker-compose.yml
├── .env.example
│
├── docs/
│   ├── DATABASE_SCHEMA.md
│   ├── MCP_DESIGN.md
│   ├── API_SPECIFICATIONS.md
│   ├── MVP_ROADMAP.md
│   └── TECH_STACK.md
│
├── backend/
│   ├── api-gateway/
│   │   └── pom.xml
│   ├── user-service/
│   │   └── pom.xml
│   ├── recommendation-service/
│   │   └── pom.xml
│   └── portfolio-service/
│       └── pom.xml
│
├── mcp-servers/
│   ├── stock-data-server/
│   ├── sentiment-server/
│   └── prediction-server/
│
├── ml-services/
│   ├── stock-prediction/
│   └── portfolio-optimizer/
│
└── infrastructure/
    ├── docker/
    ├── kubernetes/
    └── terraform/
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Java 17+
- Python 3.9+
- Node.js 18+ (frontend)

### Setup (MVP Week 1)

```bash
# 1. Clone and setup
git clone <repo>
cd claude_mcp_project

# 2. Environment setup
cp .env.example .env

# 3. Start infrastructure (PostgreSQL, Redis, Kafka, TimescaleDB)
docker-compose up -d

# 4. Run database migrations
./scripts/init-db.sh

# 5. Start backend services
cd backend/api-gateway && mvn spring-boot:run

# 6. Start MCP servers
cd mcp-servers/stock-data-server && make run
```

## 🧩 MCP Servers (MVP)

### 1. Stock Data Server
- `get_stock_price(symbol)` — Real-time stock prices
- `get_historical_data(symbol, timeframe)` — Historical OHLCV data
- `get_market_index_data(index)` — Index performance

**Tech**: Python FastAPI + yfinance/Alpha Vantage

### 2. Sentiment Server
- `get_news_sentiment(symbol)` — News sentiment analysis
- `get_social_sentiment(symbol)` — Twitter/Reddit sentiment

**Tech**: Python + HuggingFace Transformers

### 3. Prediction Server
- `predict_stock_price(symbol, days)` — Price forecasting
- `predict_market_trend(index)` — Bull/bear detection

**Tech**: Python + TensorFlow/PyTorch + LSTM/XGBoost

## 📊 Database Design

**Primary Databases**:
- **PostgreSQL**: Users, portfolios, metadata
- **TimescaleDB**: Stock price time-series (hyper-optimized)
- **MongoDB**: News, sentiment outputs, AI explanations
- **Redis**: Caching, real-time recommendations

See [DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md) for complete schema.

## 🔌 MCP Integration Flow

```
LLM (AI Orchestrator)
    ↓
MCP Client (route requests)
    ↓
MCP Servers:
  ├── StockDataServer → fetch prices/indices
  ├── SentimentServer → analyze sentiment
  ├── PredictionServer → forecast trends
  ├── PortfolioServer → build/optimize portfolio
  └── AlertServer → generate signals
    ↓
Aggregated Results → LLM Reasoning → Final Output
```

## 📈 MVP Roadmap (Weeks 1-4)

### Week 1: Foundation
- [ ] Spring Boot microservices (User, Recommendation, Portfolio)
- [ ] API Gateway setup
- [ ] PostgreSQL + Redis initialization
- [ ] Basic stock data ingestion (yfinance)

### Week 2: MCP & Data
- [ ] Stock Data MCP Server
- [ ] Sentiment MCP Server
- [ ] Kafka integration
- [ ] TimescaleDB setup

### Week 3: ML & Portfolio
- [ ] ML prediction models (LSTM, XGBoost)
- [ ] Portfolio generator logic
- [ ] MCP orchestration integration
- [ ] Basic recommendation engine

### Week 4: Integration & UI
- [ ] React dashboard scaffolding
- [ ] WebSocket real-time updates
- [ ] End-to-end AI → MCP → UI flow
- [ ] TradingView integration (optional)

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **API Gateway** | Spring Cloud Gateway |
| **Microservices** | Spring Boot |
| **MCP Orchestration** | MCP Client/Servers (Python + Java) |
| **ML/Predictions** | Python, TensorFlow, XGBoost |
| **Real-time Streaming** | Apache Kafka |
| **Databases** | PostgreSQL, TimescaleDB, MongoDB, Redis |
| **Frontend** | React/Next.js, D3.js, WebSockets |
| **DevOps** | Docker, Kubernetes, Terraform |
| **CI/CD** | GitHub Actions |

## 🔐 Security

- **MCP Isolation**: Each server runs in isolated container
- **API Authentication**: OAuth2/JWT
- **Database Encryption**: TLS for PostgreSQL/TimescaleDB
- **Secrets Management**: HashiCorp Vault
- **Rate Limiting**: Redis-based token bucket

## 📖 Documentation

- [Architecture & Design](docs/ARCHITECTURE.md)
- [Database Schema](docs/DATABASE_SCHEMA.md)
- [MCP Design](docs/MCP_DESIGN.md)
- [API Specifications](docs/API_SPECIFICATIONS.md)
- [MVP Roadmap](docs/MVP_ROADMAP.md)

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md)

## 📄 License

MIT License

---

**Questions?** Check [ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed insights.
