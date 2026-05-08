# MCP (Model Context Protocol) Design

## Overview

The MCP layer is the **central nervous system** of the entire platform. It orchestrates all external tool calls, ML models, and data sources. The LLM (AI Orchestrator) NEVER calls APIs directly—all requests route through MCP.

---

## MCP Architecture Principles

### Core Rule: No Direct API Calls

```
❌ WRONG:
LLM → yfinance API (direct)
LLM → Sentiment API (direct)

✅ CORRECT:
LLM → MCP Client
  → Stock Data MCP Server → yfinance API
  → Sentiment MCP Server → NewsAPI
  → Prediction MCP Server → ML Model
```

**Why?**
- Centralized error handling
- Consistent retry logic
- Unified authentication
- Tool versioning & updates without LLM changes
- Monitoring & logging of all external calls
- Rate limiting per service

---

## MCP Servers (MVP Phase)

### 1. Stock Data MCP Server

**Language**: Python FastAPI
**Port**: 5001
**Repository**: `mcp-servers/stock-data-server`

#### Tools Exposed

```python
@mcp.tool
def get_stock_price(symbol: str) -> dict:
    """
    Fetch current stock price
    
    Args:
        symbol: Stock ticker (e.g., "AAPL", "INFY")
    
    Returns:
        {
            "symbol": "AAPL",
            "price": 150.25,
            "change_percent": 1.25,
            "volume": 2500000,
            "timestamp": "2024-05-07T14:30:00Z"
        }
    """

@mcp.tool
def get_historical_data(symbol: str, days: int = 365) -> dict:
    """
    Fetch historical OHLCV data
    
    Args:
        symbol: Stock ticker
        days: Number of days of history
    
    Returns:
        {
            "symbol": "AAPL",
            "data": [
                {"date": "2024-05-07", "open": 149.5, "high": 151.0, "low": 149.0, "close": 150.25, "volume": 2500000},
                ...
            ]
        }
    """

@mcp.tool
def get_market_index_data(index: str) -> dict:
    """
    Fetch market index data (NASDAQ, Nifty 50, S&P 500, etc.)
    
    Args:
        index: Index code (e.g., "^NSEI" for Nifty)
    
    Returns:
        {
            "index": "^NSEI",
            "value": 21150.25,
            "change_percent": 0.85,
            "timestamp": "2024-05-07T14:30:00Z",
            "top_gainers": [...],
            "top_losers": [...]
        }
    """

@mcp.tool
def get_sector_data(sector: str, country: str = "IN") -> dict:
    """
    Fetch sector performance and constituents
    
    Args:
        sector: Sector name (IT, Banking, Pharma, etc.)
        country: Country code
    
    Returns:
        {
            "sector": "IT",
            "performance_percent": 2.5,
            "stocks": [
                {"symbol": "INFY", "price": 1850, "change_percent": 1.2},
                ...
            ]
        }
    """

@mcp.tool
def get_earnings_data(symbol: str) -> dict:
    """Fetch earnings and fundamental data"""
```

#### Integration Example

```python
# Called by MCP Client
stock_data_server = MCPServer("stock-data")
response = stock_data_server.call("get_historical_data", {
    "symbol": "INFY",
    "days": 365
})
# Response: {"symbol": "INFY", "data": [...]}
```

---

### 2. Sentiment MCP Server

**Language**: Python FastAPI
**Port**: 5002
**Repository**: `mcp-servers/sentiment-server`
**ML Models**: DistilBERT (fine-tuned on financial news)

#### Tools Exposed

```python
@mcp.tool
def get_news_sentiment(symbol: str, days: int = 7) -> dict:
    """
    Get aggregated sentiment from financial news
    
    Args:
        symbol: Stock ticker
        days: Number of days to analyze
    
    Returns:
        {
            "symbol": "AAPL",
            "sentiment_score": 0.72,  # -1.0 (very negative) to +1.0 (very positive)
            "sentiment_label": "positive",
            "articles_analyzed": 42,
            "top_themes": ["AI", "iPhone", "M3 chip"],
            "sentiment_trend": [0.65, 0.68, 0.72],  # 3-day trend
            "timestamp": "2024-05-07T14:30:00Z"
        }
    """

@mcp.tool
def get_social_sentiment(symbol: str) -> dict:
    """
    Get sentiment from Twitter/Reddit/social media
    
    Returns:
        {
            "symbol": "AAPL",
            "twitter_sentiment": 0.68,
            "reddit_sentiment": 0.65,
            "combined_score": 0.67,
            "mention_volume": 15000,
            "trending": true
        }
    """

@mcp.tool
def get_analyst_consensus(symbol: str) -> dict:
    """
    Get analyst ratings and consensus
    
    Returns:
        {
            "symbol": "AAPL",
            "rating": "BUY",
            "price_target": 180.0,
            "current_price": 150.25,
            "upside_percent": 19.8,
            "buy_count": 25,
            "hold_count": 5,
            "sell_count": 2,
            "consensus_confidence": 0.89
        }
    """

@mcp.tool
def get_sentiment_trend(symbol: str, days: int = 30) -> dict:
    """
    Get historical sentiment trend
    
    Returns: [{"date": "2024-04-07", "sentiment": 0.65}, ...]
    """
```

#### ML Pipeline

```
News API (NewsAPI, Finnhub)
    ↓
HuggingFace DistilBERT (sentiment classification)
    ↓
Aggregate scores (mean, weighted)
    ↓
Store in MongoDB
    ↓
Return to MCP Client
```

---

### 3. Prediction MCP Server

**Language**: Python FastAPI
**Port**: 5003
**Repository**: `mcp-servers/prediction-server`
**ML Models**: LSTM, XGBoost, Prophet

#### Tools Exposed

```python
@mcp.tool
def predict_stock_price(symbol: str, days: int, model: str = "auto") -> dict:
    """
    Predict future stock price
    
    Args:
        symbol: Stock ticker
        days: Number of days ahead (1-365)
        model: "lstm" (short-term), "xgboost" (medium), "prophet" (long-term), "auto"
    
    Returns:
        {
            "symbol": "INFY",
            "current_price": 1850.0,
            "predictions": [
                {"date": "2024-05-08", "price": 1865.0, "confidence": 0.92},
                {"date": "2024-05-09", "price": 1880.0, "confidence": 0.88},
                ...
            ],
            "model_used": "lstm",
            "accuracy_metric": 0.87,  # MAE or RMSE
            "confidence_interval_lower": 1800,
            "confidence_interval_upper": 1920,
            "trend": "bullish"
        }
    """

@mcp.tool
def predict_market_trend(index: str, days: int = 30) -> dict:
    """
    Predict overall market trend
    
    Returns:
        {
            "index": "^NSEI",
            "trend": "bullish",  # bullish, neutral, bearish
            "trend_strength": 0.75,
            "probability": {
                "bullish": 0.75,
                "neutral": 0.15,
                "bearish": 0.10
            }
        }
    """

@mcp.tool
def predict_volatility(symbol: str) -> dict:
    """
    Predict stock volatility
    
    Returns:
        {
            "symbol": "AAPL",
            "current_volatility": 0.24,  # annualized std dev
            "predicted_volatility": 0.28,
            "risk_level": "medium"
        }
    """

@mcp.tool
def predict_crash_risk(symbol: str) -> dict:
    """
    Predict probability of significant price drop
    
    Returns:
        {
            "symbol": "AAPL",
            "crash_probability_7d": 0.05,
            "crash_probability_30d": 0.12,
            "risk_score": 35,  # 0-100
            "warning_level": "low"
        }
    """

@mcp.tool
def predict_momentum(symbol: str) -> dict:
    """
    Predict momentum indicators
    
    Returns:
        {
            "symbol": "AAPL",
            "momentum_score": 0.85,  # 0-1
            "rsi": 72,  # Relative Strength Index
            "macd_strength": "strong_buy"
        }
    """
```

#### ML Model Selection

```python
# Automatic model selection based on timeframe
if days <= 7:
    model = LSTM()  # LSTM for short-term (better at capturing trends)
elif days <= 90:
    model = XGBoost()  # XGBoost for medium-term (more robust)
else:
    model = Prophet()  # Prophet for long-term (handles seasonality)

# Feature engineering
features = engineer_features(historical_data, technical_indicators)

# Train/predict
predictions = model.predict(features, days)
confidence = calculate_confidence(model.accuracy, recent_volatility)
```

---

### 4. Portfolio MCP Server

**Language**: Java Spring Boot / Python FastAPI
**Port**: 5004
**Repository**: `mcp-servers/portfolio-server`

#### Tools Exposed

```python
@mcp.tool
def build_portfolio(
    stocks: list[str],
    amount: float,
    risk_profile: str,
    time_horizon: str
) -> dict:
    """
    Build optimized portfolio from given stocks
    
    Args:
        stocks: List of stock symbols
        amount: Investment amount
        risk_profile: "low", "medium", "high"
        time_horizon: "intraday", "short_term", "mid_term", "long_term"
    
    Returns:
        {
            "portfolio": [
                {"symbol": "INFY", "allocation": 0.35, "amount": 3500},
                {"symbol": "TCS", "allocation": 0.30, "amount": 3000},
                {"symbol": "WIPRO", "allocation": 0.20, "amount": 2000},
                {"symbol": "HCL", "allocation": 0.15, "amount": 1500}
            ],
            "total_amount": 10000,
            "expected_return": 0.15,  # 15% annually
            "expected_return_amount": 1500,
            "risk_score": 45,  # 0-100
            "sharpe_ratio": 1.85,
            "diversification_score": 0.92
        }
    """

@mcp.tool
def optimize_portfolio(
    current_portfolio: list[dict],
    market_data: dict,
    objective: str = "max_sharpe"
) -> dict:
    """
    Optimize existing portfolio weights
    
    Args:
        objective: "max_sharpe", "min_risk", "max_return"
    
    Returns:
        {
            "optimized_portfolio": [...],
            "improvement": {
                "return_improvement_percent": 2.5,
                "risk_reduction_percent": 3.2,
                "sharpe_ratio_improvement": 0.15
            }
        }
    """

@mcp.tool
def rebalance_portfolio(
    current_portfolio: list[dict],
    current_prices: dict
) -> dict:
    """
    Suggest rebalancing to stay aligned with target allocation
    """

@mcp.tool
def simulate_portfolio(
    stocks: list[str],
    weights: list[float],
    days: int = 252
) -> dict:
    """
    Simulate portfolio performance (backtesting)
    
    Returns:
        {
            "cumulative_return": 0.25,  # 25%
            "annualized_return": 0.18,
            "max_drawdown": -0.12,
            "sharpe_ratio": 1.95,
            "sortino_ratio": 2.40,
            "monte_carlo_simulations": [...]
        }
    """
```

#### Optimization Algorithms

```python
from scipy.optimize import minimize
import numpy as np

def optimize_markowitz(expected_returns, cov_matrix, target_allocations=None):
    """
    Modern Portfolio Theory (Markowitz)
    Maximize Sharpe ratio = (R_p - R_f) / σ_p
    """
    n_assets = len(expected_returns)
    
    # Objective function: negative Sharpe ratio (minimize)
    def portfolio_sharpe(weights):
        p_return = np.sum(weights * expected_returns)
        p_std = np.sqrt(weights @ cov_matrix @ weights)
        return -(p_return / p_std)  # Risk-free rate ≈ 0 for simplicity
    
    # Constraints
    constraints = (
        {'type': 'eq', 'fun': lambda w: np.sum(w) - 1},  # weights sum to 1
    )
    
    # Bounds (0-1 for each weight)
    bounds = tuple((0, 1) for _ in range(n_assets))
    
    # Optimize
    result = minimize(portfolio_sharpe, x0=[1/n_assets]*n_assets, 
                     method='SLSQP', bounds=bounds, constraints=constraints)
    
    return result.x  # optimal weights
```

---

### 5. Alert MCP Server

**Language**: Python FastAPI
**Port**: 5005
**Repository**: `mcp-servers/alert-server`

#### Tools Exposed

```python
@mcp.tool
def generate_buy_signals(symbols: list[str]) -> dict:
    """Generate buy signals based on technical analysis"""

@mcp.tool
def generate_sell_signals(portfolio: list[dict]) -> dict:
    """Generate sell signals for current holdings"""

@mcp.tool
def risk_alerts(portfolio: list[dict]) -> dict:
    """Generate risk-based alerts"""

@mcp.tool
def news_alerts(symbols: list[str]) -> dict:
    """Alert on major news events"""
```

---

## MCP Client Implementation

### Location
`backend/recommendation-service/src/main/java/com/stock/mcp/MCPClient.java`

### Core Functionality

```java
@Component
public class MCPClient {
    
    private final RestTemplate restTemplate;
    private final MCPConfiguration config;
    private final MetricsService metrics;
    
    /**
     * Execute MCP tool call with retry logic
     */
    public <I, O> O executeTool(
        String serverName,
        String toolName,
        I input,
        Class<O> outputType
    ) throws MCPException {
        
        String url = config.getServerUrl(serverName) + "/tools/" + toolName;
        
        try {
            // Call MCP server
            HttpEntity<I> request = new HttpEntity<>(input);
            ResponseEntity<O> response = restTemplate.postForEntity(
                url, request, outputType
            );
            
            // Log success
            metrics.recordToolCall(serverName, toolName, 
                response.getStatusCode().value());
            
            return response.getBody();
            
        } catch (RestClientException e) {
            // Retry logic
            return retryWithBackoff(url, request, outputType, 3);
        }
    }
    
    /**
     * Execute multiple MCP calls in parallel
     */
    public ParallelMCPResult executeParallel(
        List<MCPToolCall> toolCalls
    ) throws MCPException {
        
        ExecutorService executor = Executors.newFixedThreadPool(
            Math.min(10, toolCalls.size())
        );
        
        List<Future<Object>> futures = toolCalls.stream()
            .map(call -> executor.submit(() -> 
                executeTool(call.serverName, call.toolName, 
                           call.input, Object.class)
            ))
            .collect(Collectors.toList());
        
        // Wait for all with timeout
        Map<String, Object> results = new HashMap<>();
        for (int i = 0; i < toolCalls.size(); i++) {
            try {
                Object result = futures.get(i).get(5, TimeUnit.SECONDS);
                results.put(toolCalls.get(i).toolName, result);
            } catch (TimeoutException e) {
                results.put(toolCalls.get(i).toolName, 
                   createFallbackResponse(toolCalls.get(i)));
            }
        }
        
        executor.shutdown();
        return new ParallelMCPResult(results);
    }
}
```

---

## MCP Orchestration Flow (User Query → Response)

### Step-by-Step Example

```
User Input:
"I have $10,000. I'm medium-risk. I like IT stocks. What should I buy for 1 year?"

↓ [1] API Gateway receives request

↓ [2] Recommendation Service analyzes query
   - Constraints: amount=$10k, risk=medium, sector=IT, horizon=1year
   - MCP tools needed: stock_data, sentiment, prediction, portfolio

↓ [3] MCP Client calls Stock Data Server (parallel)
   - get_sector_data("IT", "IN")
   - Returns: 40 IT stocks from Nifty

↓ [4] MCP Client calls Sentiment Server (parallel)
   - get_news_sentiment([list of IT stocks])
   - Returns: sentiment scores for each

↓ [5] MCP Client calls Prediction Server (parallel)
   - predict_stock_price([IT stocks], days=365)
   - Returns: 1-year price forecasts

↓ [6] Aggregate results
   - Format: [{"symbol": "INFY", "price": 1850, "1y_forecast": 2150, "sentiment": 0.72}, ...]

↓ [7] Send to LLM (Claude/GPT)
   Prompt: "Rank these 40 IT stocks by risk-adjusted return. Build 5-stock portfolio with $10k, medium risk."

↓ [8] LLM Returns Ranking & Allocation
   - Top 5: INFY (35%), TCS (30%), WIPRO (20%), HCL (10%), TECHM (5%)
   - Expected return: 15% annually

↓ [9] MCP Client calls Portfolio Server
   - simulate_portfolio([INFY, TCS, WIPRO, HCL, TECHM], [0.35, 0.30, 0.20, 0.10, 0.05], days=252)
   - Returns: backtest results, Sharpe ratio, drawdown

↓ [10] Save recommendation to PostgreSQL
   - Store in recommendations table
   - Store detailed explanation in MongoDB

↓ [11] Return to user
   {
     "portfolio": [
       {"symbol": "INFY", "allocation": 35%, "reason": "..."},
       ...
     ],
     "expected_return": "15% annually",
     "sharpe_ratio": 1.85,
     "backtest_result": {...},
     "confidence": 0.82
   }
```

---

## Error Handling & Resilience

### Circuit Breaker Pattern

```python
from circuitbreaker import circuit

@circuit(failure_threshold=5, timeout=60)
def call_stock_data_server(symbol):
    """Fails gracefully if server repeatedly fails"""
    return requests.get(f"http://stock-data:5001/price/{symbol}").json()

# If 5 failures in 60s, circuit opens and fails immediately
# Retries every 60s
```

### Timeout & Fallback

```java
// Timeout: 5 seconds per tool
// If tool times out, use cache or default response

Object result = executeTool(serverName, toolName, input, outputType)
    .withTimeout(Duration.ofSeconds(5))
    .orElse(getCachedResult(serverName, toolName))
    .orElse(getDefaultFallback());
```

---

## Monitoring MCP Calls

### Prometheus Metrics

```
# Latency
mcp_tool_latency_ms{server="stock_data", tool="get_stock_price"}
# Count
mcp_tool_calls_total{server="stock_data", tool="get_stock_price", status="success"}
# Error rate
mcp_tool_errors_total{server="stock_data"}
```

### Jaeger Distributed Tracing

```
Trace ID: abc123
├─ Span: RecommendationService.generateRecommendation (2000ms)
│  ├─ Span: MCPClient.executeParallel (1800ms)
│  │  ├─ Span: StockDataServer.getSectorData (200ms)
│  │  ├─ Span: SentimentServer.getNewsSentiment (400ms)
│  │  ├─ Span: PredictionServer.predictStockPrice (1100ms)
│  │  └─ Span: PortfolioServer.buildPortfolio (150ms)
│  └─ Span: LLMOrchestrator.rankRecommendations (100ms)
└─ Response sent (2000ms)
```

---

This MCP design ensures the entire system remains modular, testable, and easily extensible. New MCP servers can be added without changing the core LLM logic.
