# MVP Roadmap (Weeks 1-4)

## Overview

This roadmap outlines the implementation of a **production-ready MVP** for the AI Stock Market Intelligence Platform, focusing on core functionality and MCP orchestration.

---

## Week 1: Foundation & Infrastructure

### Goal
Set up backend microservices, API Gateway, databases, and core infrastructure.

### Tasks

#### 1.1 Project Setup & Configuration
- [ ] Initialize Git repository with proper .gitignore
- [ ] Set up CI/CD pipeline (GitHub Actions)
- [ ] Create project documentation (README, contributing guide)
- [ ] Set up secrets management (HashiCorp Vault or AWS Secrets Manager)

**Deliverables**: 
- GitHub repo with CI/CD configured
- Terraform variables and secrets templates

#### 1.2 Database Setup
- [ ] Provision PostgreSQL database (AWS RDS or on EC2)
- [ ] Provision Redis instance
- [ ] Create PostgreSQL schema (users, stocks, portfolios, recommendations)
- [ ] Set up initial data seeding (stock symbols, sector mappings)
- [ ] Test database connections and backups

**Deliverables**:
- PostgreSQL with schema initialized
- Redis running and tested
- Database migrations (Flyway/Liquibase)
- Backup strategy documented

#### 1.3 Spring Boot Microservices Setup

##### 1.3.1 API Gateway
- [ ] Create Spring Cloud Gateway service
- [ ] Configure routes to downstream services
- [ ] Implement JWT token validation
- [ ] Set up rate limiting (Redis-based token bucket)
- [ ] Add request logging and correlation IDs

**Stack**: Java 17, Spring Boot 3.x, Spring Cloud 2022.x

##### 1.3.2 User Service
- [ ] Create Spring Boot service
- [ ] Implement user registration endpoint
- [ ] Implement user login endpoint (OAuth2/JWT)
- [ ] Implement user profile endpoints (GET/PUT)
- [ ] Risk profile assessment logic
- [ ] Database persistence (PostgreSQL)

##### 1.3.3 Recommendation Service (MCP Client Hub)
- [ ] Create Spring Boot service
- [ ] Implement MCP Client class (orchestrator)
- [ ] Set up RestTemplate for MCP server calls
- [ ] Implement parallel tool execution
- [ ] Error handling and retry logic
- [ ] Metrics collection (Prometheus)

**Deliverables**:
- 3 Spring Boot services running
- API Gateway routing correctly
- Health check endpoints
- Docker containerization

#### 1.4 Docker & Docker Compose
- [ ] Create Dockerfile for each service
- [ ] Create docker-compose.yml for local development
- [ ] Include PostgreSQL, Redis, all microservices
- [ ] Add Prometheus and Grafana services
- [ ] Test end-to-end local setup

**Deliverables**:
```bash
docker-compose up  # Entire stack runs locally
```

#### 1.5 Stock Data Ingestion (Batch)
- [ ] Set up batch job to ingest stock symbols
- [ ] Data sources: yfinance, Alpha Vantage
- [ ] Scheduler: Apache Airflow or Spring Batch
- [ ] Populate stocks table in PostgreSQL
- [ ] Initial price data import

**Deliverables**:
- `stocks` table populated with ~5000 global stocks
- Price data dated 1 year back

### Acceptance Criteria
- [ ] All 3 services start successfully
- [ ] PostgreSQL and Redis are healthy
- [ ] API Gateway routes requests correctly
- [ ] Docker Compose runs entire stack locally
- [ ] Stock symbols loaded in database

---

## Week 2: MCP Servers & Real-Time Data

### Goal
Implement first 3 MCP servers (Stock Data, Sentiment, basic Prediction) and integrate Kafka for streaming.

### Tasks

#### 2.1 Stock Data MCP Server (Python FastAPI)
- [ ] Create FastAPI project structure
- [ ] Implement `get_stock_price()` tool (yfinance)
- [ ] Implement `get_historical_data()` tool (yfinance)
- [ ] Implement `get_market_index_data()` tool (yfinance)
- [ ] Implement `get_sector_data()` tool
- [ ] Add error handling and retry logic
- [ ] Add Prometheus metrics
- [ ] Docker containerization

**Tech Stack**: Python 3.9+, FastAPI, yfinance, Prometheus client

**Deliverables**:
```bash
POST /tools/get_stock_price
{
  "symbol": "INFY"
}
→
{
  "symbol": "INFY",
  "price": 1850.0,
  "timestamp": "2024-05-07T14:30:00Z"
}
```

#### 2.2 Sentiment MCP Server (Python FastAPI)
- [ ] Create FastAPI project structure
- [ ] Set up HuggingFace Transformers (DistilBERT for sentiment)
- [ ] Implement `get_news_sentiment()` tool
  - [ ] Integrate NewsAPI for news fetching
  - [ ] Sentiment classification on news articles
  - [ ] Aggregate scores
- [ ] Implement `get_social_sentiment()` tool
  - [ ] Optional: Twitter API integration
  - [ ] Score aggregation
- [ ] Caching (Redis) for sentiment scores
- [ ] Docker containerization

**Tech Stack**: Python, FastAPI, HuggingFace, Transformers, NewsAPI

**Deliverables**:
```bash
POST /tools/get_news_sentiment
{
  "symbol": "AAPL",
  "days": 7
}
→
{
  "symbol": "AAPL",
  "sentiment_score": 0.72,
  "articles_analyzed": 42
}
```

#### 2.3 TimescaleDB Setup
- [ ] Provision TimescaleDB (AWS RDS or EC2)
- [ ] Create hyper-tables for stock prices
- [ ] Set up compression policies (chunks > 7 days)
- [ ] Initial historical data migration from PostgreSQL
- [ ] Test query performance vs PostgreSQL

**Deliverables**:
- TimescaleDB with stock_prices hyper-table ready
- Sample queries <100ms for 1-year of data

#### 2.4 Kafka & Real-Time Streaming
- [ ] Set up Apache Kafka cluster (AWS MSK or local)
- [ ] Create Kafka topics:
  - `stock-prices` (1 min updates)
  - `news-events` (new articles)
  - `recommendations-queue` (pending recommendations)
- [ ] Producer: Stock price updater service
  - [ ] Scheduled daily: 9 AM-4 PM market hours
  - [ ] Publish to `stock-prices` topic
- [ ] Consumers:
  - [ ] TimescaleDB consumer (writes prices)
  - [ ] Redis cache updater
  - [ ] Alert trigger consumer

**Deliverables**:
- Kafka topics created and tested
- Stock price updates flowing to TimescaleDB

#### 2.5 MCP Client Integration (Recommendation Service)
- [ ] Update Recommendation Service to call Stock Data MCP Server
- [ ] Update Recommendation Service to call Sentiment MCP Server
- [ ] Parallel execution of MCP tools
- [ ] Result aggregation
- [ ] Caching of MCP responses (1 min TTL)

**Test Scenario**:
```
POST /api/recommendations/analyze
{
  "symbol": "INFY",
  "timeframe": "1-year"
}
→
Calls: StockDataServer + SentimentServer in parallel
Response: Combined data with prices + sentiment
```

### Acceptance Criteria
- [ ] Stock Data Server running and responding
- [ ] Sentiment Server running with HF model loaded
- [ ] TimescaleDB operational with hyper-tables
- [ ] Kafka topics created and streaming data
- [ ] Recommendation Service orchestrates 2 MCP servers
- [ ] All services dockerized and in docker-compose

---

## Week 3: ML Models & Portfolio Construction

### Goal
Implement ML prediction models and portfolio optimization logic.

### Tasks

#### 3.1 Prediction MCP Server (Python FastAPI)
- [ ] Create FastAPI project structure
- [ ] Set up ML training pipeline
  - [ ] Feature engineering (technical indicators)
  - [ ] LSTM model for short-term (1-7 days)
  - [ ] XGBoost model for medium-term (7-30 days)
  - [ ] Prophet model for long-term (30+ days)
- [ ] Implement `predict_stock_price()` tool
  - [ ] Smart model selection based on timeframe
  - [ ] Confidence score calculation
  - [ ] Confidence intervals (upper/lower bounds)
- [ ] Implement `predict_market_trend()` tool
- [ ] Model serving (TensorFlow Serving or local inference)
- [ ] Caching predictions for 1 hour
- [ ] Docker containerization

**Tech Stack**: Python, FastAPI, TensorFlow, XGBoost, Prophet

**Deliverables**:
```bash
POST /tools/predict_stock_price
{
  "symbol": "INFY",
  "days": 30
}
→
{
  "symbol": "INFY",
  "predictions": [
    {"date": "2024-05-08", "price": 1865.0, "confidence": 0.92},
    ...
  ],
  "model_used": "xgboost"
}
```

#### 3.2 Portfolio MCP Server (Java Spring Boot)
- [ ] Create Spring Boot service
- [ ] Implement `build_portfolio()` tool
  - [ ] Input: stocks list, amount, risk profile, horizon
  - [ ] Markowitz optimization (scipy in separate Python service)
  - [ ] Output: stock allocation percentages
- [ ] Implement `optimize_portfolio()` tool
- [ ] Implement `simulate_portfolio()` tool (backtesting)
  - [ ] Historical simulation
  - [ ] Calculate: return, volatility, Sharpe ratio, max drawdown
- [ ] Call efficient frontier calculation

**Tech Stack**: Java Spring Boot, Python scipy/numpy for math

**Deliverables**:
```bash
POST /tools/build_portfolio
{
  "stocks": ["INFY", "TCS", "WIPRO"],
  "amount": 10000,
  "risk_profile": "medium"
}
→
{
  "portfolio": [
    {"symbol": "INFY", "allocation": 0.35},
    {"symbol": "TCS", "allocation": 0.30},
    {"symbol": "WIPRO", "allocation": 0.35}
  ]
}
```

#### 3.3 MongoDB Setup
- [ ] Provision MongoDB (AWS Atlas or EC2)
- [ ] Schema design:
  - [ ] `news` collection
  - [ ] `sentiment` collection
  - [ ] `ml_predictions` collection
  - [ ] `recommendations_detail` collection (with explanations)
- [ ] Create indexes for queries

**Deliverables**:
- MongoDB with collections ready
- Indexes optimized for common queries

#### 3.4 MCP Client Enhancement
- [ ] Add Prediction Server integration
- [ ] Add Portfolio Server integration
- [ ] Parallel execution of 4 MCP servers
- [ ] Result aggregation and formatting for LLM

#### 3.5 Recommendation Engine (Business Logic)
- [ ] Orchestrate MCP servers:
  1. Stock Data → get sector stocks
  2. Sentiment → analyze sentiment
  3. Prediction → forecast prices
  4. Portfolio → optimize allocation
- [ ] Rank recommendations by score
- [ ] Generate explanation text (explainable AI)
- [ ] Save to PostgreSQL + MongoDB

### Acceptance Criteria
- [ ] Prediction MCP Server responding with forecasts
- [ ] Portfolio MCP Server optimizing allocations
- [ ] MongoDB operational with collections
- [ ] MCP Client calling 4 servers in parallel
- [ ] Recommendation engine generating ranked portfolio
- [ ] All in docker-compose

---

## Week 4: Integration & UI Foundation

### Goal
Complete end-to-end integration and basic React dashboard.

### Tasks

#### 4.1 LLM Integration (Claude/GPT)
- [ ] Set up LLM API (OpenAI or Anthropic)
- [ ] Implement prompt engineering
  - Template: "Given these stocks and their metrics, rank them and build portfolio"
- [ ] Parse LLM output (JSON)
- [ ] Add reasoning/explanation to recommendations
- [ ] Caching of LLM responses (complex hashing on input)

**Deliverables**:
```python
# Recommendation Service calls LLM
llm_response = call_llm(prompt=f"""
Given {stock_metrics}:
1. Rank by risk-adjusted return
2. Build {allocation_count}-stock portfolio
3. Explain each selection
""")

# Parse response for portfolio + explanations
```

#### 4.2 React Dashboard (Scaffolding)
- [ ] Create React/Next.js project
- [ ] Authentication page (login/register)
- [ ] User profile page
- [ ] Portfolio recommendation page
  - [ ] Input form (amount, risk, sector, horizon)
  - [ ] Submit to `/api/recommendations/generate`
  - [ ] Display recommended portfolio
  - [ ] Show explanation for each stock
- [ ] WebSocket connection for real-time updates

**Tech Stack**: React/Next.js, TypeScript, TailwindCSS

**Deliverables**:
- Basic React app running at http://localhost:3000
- User can input preferences and get recommendations

#### 4.3 WebSocket Real-Time Updates
- [ ] Set up WebSocket server in API Gateway / separate service
- [ ] Broadcast stock price updates to connected users
- [ ] Subscribe to portfolio updates
- [ ] React component subscribes to WebSocket

**Deliverables**:
```jsx
// React component
useEffect(() => {
  const socket = new WebSocket('ws://localhost:8080/prices');
  socket.onmessage = (event) => {
    setStockPrices(JSON.parse(event.data));
  };
}, []);
```

#### 4.4 TradingView Chart Integration (Optional)
- [ ] Embed TradingView Lightweight Charts
- [ ] Display stock price history
- [ ] Show technical indicators (RSI, MACD)
- [ ] Interactive zoom/pan

**Deliverables**:
- Interactive chart on portfolio page

#### 4.5 End-to-End Testing
- [ ] Postman/Insomnia API testing
  - [ ] User registration
  - [ ] Login (JWT token)
  - [ ] Recommendation generation (full MCP flow)
  - [ ] Portfolio creation and retrieval
- [ ] Load testing with JMeter
  - [ ] Simulate 100 concurrent users
  - [ ] Check latency and error rates
- [ ] Functional testing (manual + automated Selenium)

**Deliverables**:
- API testing collection
- Load test report
- End-to-end test scenarios

#### 4.6 Documentation & Deployment
- [ ] API documentation (Swagger/OpenAPI)
- [ ] Deployment guide (Docker Compose → Kubernetes)
- [ ] Environment configuration (.env.example)
- [ ] Disaster recovery plan
- [ ] Monitoring setup (Prometheus + Grafana)
  - [ ] Dashboards for system health
  - [ ] Alerts for failures

**Deliverables**:
- Complete API docs
- Deployment runbook
- Monitoring dashboard

#### 4.7 Production Build & CI/CD
- [ ] Build all Docker images
- [ ] Push to Docker registry
- [ ] Set up Kubernetes manifests (optional for Week 4)
- [ ] GitHub Actions CI/CD pipeline
  - [ ] Code quality checks (SonarQube)
  - [ ] Unit + integration tests
  - [ ] Docker build & push
  - [ ] Deployment to staging

### Acceptance Criteria
- [ ] End-to-end flow: User → API → MCP → LLM → Portfolio → UI
- [ ] React dashboard displaying recommendations
- [ ] All services in docker-compose working
- [ ] API documentation complete
- [ ] Load tests passing (100 concurrent users)
- [ ] CI/CD pipeline automated

---

## Week-by-Week Dependency Graph

```
Week 1: Foundation
├─ Databases (PostgreSQL, Redis)
├─ Microservices (API Gateway, User, Recommendation)
└─ Docker setup

Week 2: Data Layer
├─ Stock Data Server (MCP)
├─ Sentiment Server (MCP)
├─ TimescaleDB
└─ Kafka streaming
   (depends on Week 1: Services infrastructure)

Week 3: ML & Intelligence
├─ Prediction Server (MCP)
├─ Portfolio Server (MCP)
├─ MongoDB
└─ Recommendation engine orchestration
   (depends on Week 2: All MCP servers)

Week 4: Integration & UI
├─ LLM integration
├─ React dashboard
├─ WebSocket real-time
├─ End-to-end testing
└─ Deployment & monitoring
   (depends on Week 3: Complete MCP orchestration)
```

---

## Resource Allocation

| Component | Developer Count | Skill Level | Week 1 | Week 2 | Week 3 | Week 4 |
|-----------|-----------------|------------|--------|--------|--------|--------|
| Backend (Java) | 2 | Senior | Full | Full | 50% | 25% |
| Python (MCP) | 2 | Mid | - | Full | Full | 25% |
| ML (PyTorch/TF) | 1 | Senior | - | - | Full | 25% |
| Frontend (React) | 1 | Mid | - | - | - | Full |
| DevOps/Infrastructure | 1 | Senior | Full | 50% | 25% | 25% |
| QA/Testing | 1 | Mid | 25% | 25% | 50% | Full |

---

## Success Metrics

### Week 1
- [ ] 3 microservices deployed and healthy
- [ ] PostgreSQL + Redis operational
- [ ] Docker Compose runs entire stack
- [ ] ~5000 stocks loaded

### Week 2
- [ ] Stock Data Server: <500ms response time
- [ ] Sentiment Server: <2s response time (BERT inference)
- [ ] RealTime Kafka streaming working
- [ ] TimescaleDB queries: <100ms for 1-year data

### Week 3
- [ ] Prediction Server: <3s response time
- [ ] Portfolio optimization: <1s
- [ ] Portfolio backtesting: <2s
- [ ] End-to-end MCP orchestration: <10s

### Week 4
- [ ] End-to-end user flow: <15s (UI → API → MCP → LLM → Response)
- [ ] React app deployed
- [ ] 100 concurrent users: <2s avg latency
- [ ] Zero critical bugs in production

---

## Post-MVP (Weeks 5-8)

- [ ] Advanced ML models (ensemble models, neural networks)
- [ ] Market crash prediction system
- [ ] Portfolio backtesting engine (historical)
- [ ] What-if scenario simulator
- [ ] Mobile app (React Native)
- [ ] Hedge fund integration
- [ ] Multi-user portfolio collaboration
- [ ] Advanced charting (TradingView Pro)
