"""
Integration tests verifying MCP servers respond correctly
to the exact payloads that the AI Orchestrator sends them.
Uses respx to intercept httpx calls in McpClient.
"""
import pytest
import httpx
import respx
import sys
from unittest.mock import MagicMock

sys.path.insert(0, "../../ai-orchestrator")


@pytest.fixture
def settings():
    s = MagicMock()
    s.mcp_stock_data_url = "http://stock-data:5001"
    s.mcp_sentiment_url = "http://sentiment:5002"
    s.mcp_prediction_url = "http://prediction:5003"
    s.mcp_portfolio_url = "http://portfolio:5004"
    s.mcp_technical_url = "http://technical:5005"
    s.mcp_alert_url = "http://alert:5006"
    return s


@pytest.fixture
def client(settings):
    from mcp_client import McpClient
    return McpClient(settings)


# ── Stock Data tools ──────────────────────────────────────────────

@pytest.mark.asyncio
@respx.mock
async def test_get_stock_price_full_flow(client):
    expected = {
        "symbol": "RELIANCE",
        "price": 2850.75,
        "change_percent": 1.23,
        "volume": 1_200_000,
        "timestamp": "2025-01-01T10:00:00",
    }
    respx.post("http://stock-data:5001/tools/get_stock_price").mock(
        return_value=httpx.Response(200, json=expected)
    )
    result = await client.call_tool("get_stock_price", {"symbol": "RELIANCE.NS"})
    assert result["symbol"] == "RELIANCE"
    assert result["price"] == 2850.75
    assert "change_percent" in result


@pytest.mark.asyncio
@respx.mock
async def test_get_historical_data_full_flow(client):
    expected = {
        "symbol": "TCS",
        "data": [
            {"date": "2024-01-01", "open": 3800.0, "high": 3850.0,
             "low": 3780.0, "close": 3820.0, "volume": 500_000}
        ]
    }
    respx.post("http://stock-data:5001/tools/get_historical_data").mock(
        return_value=httpx.Response(200, json=expected)
    )
    result = await client.call_tool("get_historical_data", {"symbol": "TCS.NS", "days": 30})
    assert result["symbol"] == "TCS"
    assert len(result["data"]) == 1
    assert result["data"][0]["close"] == 3820.0


@pytest.mark.asyncio
@respx.mock
async def test_get_market_index_nifty50(client):
    expected = {
        "index": "NIFTY50",
        "symbol": "^NSEI",
        "value": 22475.85,
        "change_percent": 0.64,
        "timestamp": "2025-01-01T10:00:00",
    }
    respx.post("http://stock-data:5001/tools/get_market_index_data").mock(
        return_value=httpx.Response(200, json=expected)
    )
    result = await client.call_tool("get_market_index_data", {"index": "NIFTY50"})
    assert result["index"] == "NIFTY50"
    assert result["value"] == 22475.85


# ── Technical Analysis tools ──────────────────────────────────────

@pytest.mark.asyncio
@respx.mock
async def test_get_technical_indicators_full_flow(client):
    expected = {
        "symbol": "INFY",
        "rsi": 48.5,
        "macd": 12.3,
        "macd_signal": 10.1,
        "sma_20": 1720.0,
        "sma_50": 1700.0,
        "signals": {"overall": "BUY", "breakdown": []},
    }
    respx.post("http://technical:5005/tools/get_technical_indicators").mock(
        return_value=httpx.Response(200, json=expected)
    )
    result = await client.call_tool("get_technical_indicators", {"symbol": "INFY.NS", "period": 14})
    assert result["symbol"] == "INFY"
    assert 0 <= result["rsi"] <= 100
    assert result["signals"]["overall"] == "BUY"


@pytest.mark.asyncio
@respx.mock
async def test_get_rsi_routing(client):
    respx.post("http://technical:5005/tools/get_rsi").mock(
        return_value=httpx.Response(200, json={"symbol": "WIPRO", "rsi": 62.1, "period": 14})
    )
    result = await client.call_tool("get_rsi", {"symbol": "WIPRO.NS"})
    assert result["rsi"] == 62.1


@pytest.mark.asyncio
@respx.mock
async def test_get_macd_routing(client):
    respx.post("http://technical:5005/tools/get_macd").mock(
        return_value=httpx.Response(200, json={
            "symbol": "HDFCBANK",
            "macd": 8.5,
            "signal": 6.2,
            "histogram": 2.3,
            "crossover": "BULLISH",
        })
    )
    result = await client.call_tool("get_macd", {"symbol": "HDFCBANK.NS"})
    assert result["crossover"] == "BULLISH"


# ── Portfolio tools ───────────────────────────────────────────────

@pytest.mark.asyncio
@respx.mock
async def test_build_portfolio_routing(client):
    expected = {
        "portfolio": [
            {"symbol": "RELIANCE.NS", "weight": 0.4, "allocation": 40000},
            {"symbol": "TCS.NS", "weight": 0.3, "allocation": 30000},
            {"symbol": "HDFC.NS", "weight": 0.3, "allocation": 30000},
        ],
        "total_investment": 100000,
        "expected_return": 0.18,
    }
    respx.post("http://portfolio:5004/tools/build_portfolio").mock(
        return_value=httpx.Response(200, json=expected)
    )
    result = await client.call_tool("build_portfolio", {
        "symbols": ["RELIANCE.NS", "TCS.NS", "HDFC.NS"],
        "total_investment": 100000,
        "risk_profile": "MEDIUM",
    })
    assert len(result["portfolio"]) == 3
    total_weight = sum(p["weight"] for p in result["portfolio"])
    assert abs(total_weight - 1.0) < 0.01


# ── Alert tools ───────────────────────────────────────────────────

@pytest.mark.asyncio
@respx.mock
async def test_generate_buy_sell_signals_routing(client):
    expected = {
        "signals": [
            {"symbol": "RELIANCE", "action": "BUY", "score": 8, "rsi": 45.0},
            {"symbol": "TCS", "action": "HOLD", "score": 5, "rsi": 58.0},
        ]
    }
    respx.post("http://alert:5006/tools/generate_buy_sell_signals").mock(
        return_value=httpx.Response(200, json=expected)
    )
    result = await client.call_tool("generate_buy_sell_signals", {
        "symbols": ["RELIANCE.NS", "TCS.NS"],
        "risk_profile": "MEDIUM",
    })
    assert len(result["signals"]) == 2
    actions = {s["symbol"]: s["action"] for s in result["signals"]}
    assert actions["RELIANCE"] == "BUY"


# ── Error propagation ─────────────────────────────────────────────

@pytest.mark.asyncio
@respx.mock
async def test_mcp_404_propagates_gracefully(client):
    respx.post("http://stock-data:5001/tools/get_stock_price").mock(
        return_value=httpx.Response(404, json={"detail": "Stock not found"})
    )
    result = await client.call_tool("get_stock_price", {"symbol": "FAKEXYZ"})
    assert "error" in result
    assert "404" in result["error"]


@pytest.mark.asyncio
@respx.mock
async def test_mcp_timeout_does_not_crash_orchestrator(client):
    respx.post("http://stock-data:5001/tools/get_stock_price").mock(
        side_effect=httpx.TimeoutException("timeout")
    )
    result = await client.call_tool("get_stock_price", {"symbol": "TCS"})
    assert result["error"] == "timeout"
    assert result["tool"] == "get_stock_price"


# ── Health check ──────────────────────────────────────────────────

@pytest.mark.asyncio
@respx.mock
async def test_health_check_all_servers(client):
    for url in [
        "http://stock-data:5001/health",
        "http://sentiment:5002/health",
        "http://prediction:5003/health",
        "http://portfolio:5004/health",
        "http://technical:5005/health",
        "http://alert:5006/health",
    ]:
        respx.get(url).mock(
            return_value=httpx.Response(200, json={"status": "healthy"})
        )

    result = await client.health_check_all()
    assert len(result) == 6
    assert all(v == "healthy" for v in result.values())
