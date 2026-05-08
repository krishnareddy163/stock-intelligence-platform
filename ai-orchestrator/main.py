"""
AI Orchestrator - Central MCP Client
Routes user queries through Claude API → MCP Servers → Structured output
"""
import asyncio
import json
import logging
import time
import anthropic
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from config import settings
from mcp_client import McpClient
from prometheus_client import Counter, Histogram, generate_latest
from fastapi.responses import PlainTextResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Orchestrator", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

REQUEST_COUNT = Counter("orchestrator_requests_total", "Total requests", ["endpoint", "status"])
REQUEST_LATENCY = Histogram("orchestrator_request_latency_seconds", "Request latency", ["endpoint"])

claude_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
mcp = McpClient(settings)


class AnalysisRequest(BaseModel):
    user_id: str
    query: str
    country: str = "US"
    index: str = "NASDAQ"
    investment_amount: float = 10000.0
    risk_profile: str = "MEDIUM"
    time_horizon: str = "LONG_TERM"
    preferred_sectors: list[str] = []
    strategy: str = "GROWTH"


class ChatRequest(BaseModel):
    user_id: str
    message: str
    conversation_history: list[dict] = []


TOOLS = [
    {
        "name": "get_stock_price",
        "description": "Get current price and change % for a stock symbol",
        "input_schema": {
            "type": "object",
            "properties": {"symbol": {"type": "string", "description": "Stock ticker symbol (e.g. AAPL, RELIANCE.NS)"}},
            "required": ["symbol"],
        },
    },
    {
        "name": "get_historical_data",
        "description": "Get historical OHLCV data for a stock",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string"},
                "days": {"type": "integer", "description": "Number of days of history (default 365)"},
            },
            "required": ["symbol"],
        },
    },
    {
        "name": "get_market_index_data",
        "description": "Get data for a market index (NASDAQ, SP500, NIFTY50, SENSEX, NIKKEI, FTSE)",
        "input_schema": {
            "type": "object",
            "properties": {"index": {"type": "string", "description": "Index name"}},
            "required": ["index"],
        },
    },
    {
        "name": "get_technical_indicators",
        "description": "Get RSI, MACD, moving averages and Bollinger Bands for a stock",
        "input_schema": {
            "type": "object",
            "properties": {"symbol": {"type": "string"}, "period": {"type": "integer", "default": 14}},
            "required": ["symbol"],
        },
    },
    {
        "name": "get_news_sentiment",
        "description": "Get aggregated news sentiment score (-1 to 1) and top headlines for a stock",
        "input_schema": {
            "type": "object",
            "properties": {"symbol": {"type": "string"}, "days": {"type": "integer", "default": 7}},
            "required": ["symbol"],
        },
    },
    {
        "name": "predict_stock_price",
        "description": "ML price prediction for next 7/30/90 days using LSTM + XGBoost ensemble",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string"},
                "forecast_days": {"type": "integer", "description": "7, 30, or 90"},
            },
            "required": ["symbol", "forecast_days"],
        },
    },
    {
        "name": "predict_market_trend",
        "description": "Predict overall market trend (BULLISH/BEARISH/NEUTRAL) for an index",
        "input_schema": {
            "type": "object",
            "properties": {"index": {"type": "string"}, "days": {"type": "integer", "default": 30}},
            "required": ["index"],
        },
    },
    {
        "name": "build_portfolio",
        "description": "Build an optimized portfolio given stocks, amount, risk profile, and strategy",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbols": {"type": "array", "items": {"type": "string"}},
                "total_investment": {"type": "number"},
                "risk_profile": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH"]},
                "strategy": {"type": "string", "enum": ["GROWTH", "VALUE", "DIVIDEND", "MOMENTUM", "HYBRID"]},
            },
            "required": ["symbols", "total_investment", "risk_profile"],
        },
    },
    {
        "name": "generate_buy_sell_signals",
        "description": "Generate actionable BUY/SELL/HOLD signals based on technical + sentiment analysis",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbols": {"type": "array", "items": {"type": "string"}},
                "risk_profile": {"type": "string"},
            },
            "required": ["symbols"],
        },
    },
]

SYSTEM_PROMPT = """You are an elite AI financial analyst and portfolio manager with 20+ years of experience
across global markets (US, India, Japan, UK, Europe). You have deep expertise in:
- Technical analysis (RSI, MACD, Bollinger Bands, Moving Averages)
- Fundamental analysis (P/E, EPS growth, market cap, sector trends)
- Quantitative modeling (portfolio optimization, risk-adjusted returns)
- Global macroeconomics and sector rotation

You orchestrate specialized financial tools to deliver institutional-grade insights to retail investors.

BEHAVIOR RULES:
1. Always use multiple tools to cross-validate before making recommendations
2. Provide specific numbers, not vague advice
3. Explain the WHY behind every recommendation (Explainable AI)
4. Always include risk warnings appropriate to the user's risk profile
5. Structure output as: Executive Summary → Key Findings → Ranked Recommendations → Portfolio → Risk Factors

TOOL USAGE STRATEGY:
- Start with market index data to understand macro context
- Check technical indicators before any stock recommendation
- Always validate with sentiment data
- Use ML predictions to confirm direction (not as sole basis)
- Build the portfolio LAST, after all analysis is complete
"""


async def execute_tool(tool_name: str, tool_input: dict) -> dict:
    """Route tool calls to appropriate MCP servers"""
    start = time.time()
    try:
        result = await mcp.call_tool(tool_name, tool_input)
        latency = int((time.time() - start) * 1000)
        logger.info(f"Tool {tool_name} completed in {latency}ms")
        return result
    except Exception as e:
        logger.error(f"Tool {tool_name} failed: {e}")
        return {"error": str(e), "tool": tool_name}


async def run_agentic_loop(messages: list[dict], system: str = SYSTEM_PROMPT) -> dict:
    """Agentic loop: Claude calls tools until it produces a final answer"""
    tool_calls_log = []

    for iteration in range(10):  # max 10 tool-call rounds
        response = claude_client.messages.create(
            model=settings.claude_model,
            max_tokens=4096,
            system=system,
            tools=TOOLS,
            messages=messages,
        )

        # Collect text blocks
        text_parts = [b.text for b in response.content if b.type == "text"]

        if response.stop_reason == "end_turn":
            return {
                "response": "\n".join(text_parts),
                "tool_calls": tool_calls_log,
                "iterations": iteration + 1,
            }

        if response.stop_reason != "tool_use":
            break

        # Execute all tool calls in parallel
        tool_use_blocks = [b for b in response.content if b.type == "tool_use"]
        tasks = [execute_tool(b.name, b.input) for b in tool_use_blocks]
        results = await asyncio.gather(*tasks)

        tool_results = []
        for block, result in zip(tool_use_blocks, results):
            tool_calls_log.append({"tool": block.name, "input": block.input, "output": result})
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps(result),
            })

        # Append assistant response + tool results to conversation
        messages = messages + [
            {"role": "assistant", "content": response.content},
            {"role": "user", "content": tool_results},
        ]

    return {"response": "Analysis complete.", "tool_calls": tool_calls_log, "iterations": 10}


@app.post("/analyze")
async def analyze_market(req: AnalysisRequest):
    """Full market analysis with portfolio generation"""
    start = time.time()
    REQUEST_COUNT.labels(endpoint="/analyze", status="started").inc()

    horizon_map = {"INTRADAY": 1, "SHORT_TERM": 7, "MID_TERM": 30, "LONG_TERM": 90}
    forecast_days = horizon_map.get(req.time_horizon, 30)

    sector_context = f"Preferred sectors: {', '.join(req.preferred_sectors)}" if req.preferred_sectors else "No sector preference"

    user_message = f"""
Perform a comprehensive market analysis and portfolio construction for this investor:

INVESTOR PROFILE:
- Country: {req.country}
- Target Index: {req.index}
- Investment Amount: ${req.investment_amount:,.2f}
- Risk Profile: {req.risk_profile}
- Time Horizon: {req.time_horizon} ({forecast_days} days)
- Strategy: {req.strategy}
- {sector_context}

QUERY: {req.query}

Please:
1. Analyze the {req.index} market index first
2. Identify the top 5–8 stocks worth analyzing in {req.country}
3. For each: get price, technical indicators, sentiment, and ML prediction
4. Generate buy/sell signals
5. Build an optimized portfolio with the ${req.investment_amount:,.2f} budget
6. Provide detailed explanations for each recommendation

Deliver institutional-quality analysis with specific numbers and actionable insights.
""".strip()

    messages = [{"role": "user", "content": user_message}]

    try:
        result = await run_agentic_loop(messages)
        latency = int((time.time() - start) * 1000)
        REQUEST_COUNT.labels(endpoint="/analyze", status="success").inc()
        return {
            "user_id": req.user_id,
            "analysis": result["response"],
            "tool_calls": result["tool_calls"],
            "iterations": result["iterations"],
            "latency_ms": latency,
        }
    except Exception as e:
        REQUEST_COUNT.labels(endpoint="/analyze", status="error").inc()
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat")
async def financial_chat(req: ChatRequest):
    """Conversational financial advisor endpoint"""
    start = time.time()

    messages = req.conversation_history + [{"role": "user", "content": req.message}]

    try:
        result = await run_agentic_loop(messages)
        return {
            "user_id": req.user_id,
            "response": result["response"],
            "tool_calls_count": len(result["tool_calls"]),
            "latency_ms": int((time.time() - start) * 1000),
        }
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/quick-scan")
async def quick_stock_scan(symbols: list[str], risk_profile: str = "MEDIUM"):
    """Quick multi-stock scan — signals only, no portfolio construction"""
    start = time.time()

    messages = [{
        "role": "user",
        "content": f"Quick scan for these stocks: {', '.join(symbols)}. "
                   f"Investor risk profile: {risk_profile}. "
                   "Get technical indicators, sentiment, and generate buy/sell signals for each. "
                   "Return a ranked list with brief rationale.",
    }]

    result = await run_agentic_loop(messages)
    return {
        "scan": result["response"],
        "latency_ms": int((time.time() - start) * 1000),
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "model": settings.claude_model}


@app.get("/metrics")
async def metrics():
    return PlainTextResponse(generate_latest())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000, reload=False)
