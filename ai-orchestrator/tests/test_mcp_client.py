"""Unit tests for McpClient — tool routing, timeouts, HTTP errors, health checks."""
import pytest
import httpx
import respx
from unittest.mock import MagicMock
from mcp_client import McpClient


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
def mcp_client(settings):
    return McpClient(settings)


@pytest.mark.asyncio
async def test_call_tool_routes_stock_price(mcp_client):
    with respx.mock:
        respx.post("http://stock-data:5001/tools/get_stock_price").mock(
            return_value=httpx.Response(200, json={"symbol": "RELIANCE", "price": 2850.0})
        )
        result = await mcp_client.call_tool("get_stock_price", {"symbol": "RELIANCE"})
    assert result["symbol"] == "RELIANCE"
    assert result["price"] == 2850.0


@pytest.mark.asyncio
async def test_call_tool_routes_technical_indicators(mcp_client):
    with respx.mock:
        respx.post("http://technical:5005/tools/get_technical_indicators").mock(
            return_value=httpx.Response(200, json={"symbol": "TCS", "rsi": 55.2})
        )
        result = await mcp_client.call_tool("get_technical_indicators", {"symbol": "TCS"})
    assert result["rsi"] == 55.2


@pytest.mark.asyncio
async def test_call_tool_routes_sentiment(mcp_client):
    with respx.mock:
        respx.post("http://sentiment:5002/tools/get_news_sentiment").mock(
            return_value=httpx.Response(200, json={"symbol": "INFY", "sentiment": "POSITIVE"})
        )
        result = await mcp_client.call_tool("get_news_sentiment", {"symbol": "INFY"})
    assert result["sentiment"] == "POSITIVE"


@pytest.mark.asyncio
async def test_call_tool_unknown_tool(mcp_client):
    result = await mcp_client.call_tool("nonexistent_tool", {})
    assert "error" in result
    assert "Unknown tool" in result["error"]


@pytest.mark.asyncio
async def test_call_tool_timeout_returns_error(mcp_client):
    with respx.mock:
        respx.post("http://stock-data:5001/tools/get_stock_price").mock(
            side_effect=httpx.TimeoutException("timed out")
        )
        result = await mcp_client.call_tool("get_stock_price", {"symbol": "TCS"})
    assert result["error"] == "timeout"
    assert result["tool"] == "get_stock_price"


@pytest.mark.asyncio
async def test_call_tool_http_500_returns_error(mcp_client):
    with respx.mock:
        respx.post("http://stock-data:5001/tools/get_stock_price").mock(
            return_value=httpx.Response(500, json={"detail": "Internal error"})
        )
        result = await mcp_client.call_tool("get_stock_price", {"symbol": "HDFC"})
    assert "HTTP 500" in result["error"]


@pytest.mark.asyncio
async def test_call_tool_http_404_returns_error(mcp_client):
    with respx.mock:
        respx.post("http://stock-data:5001/tools/get_stock_price").mock(
            return_value=httpx.Response(404, json={"detail": "Not found"})
        )
        result = await mcp_client.call_tool("get_stock_price", {"symbol": "UNKNOWN"})
    assert "HTTP 404" in result["error"]


@pytest.mark.asyncio
async def test_call_tool_connection_error_returns_error(mcp_client):
    with respx.mock:
        respx.post("http://stock-data:5001/tools/get_stock_price").mock(
            side_effect=httpx.ConnectError("connection refused")
        )
        result = await mcp_client.call_tool("get_stock_price", {"symbol": "WIPRO"})
    assert "error" in result


@pytest.mark.asyncio
async def test_health_check_all_healthy(mcp_client):
    with respx.mock:
        for url in [
            "http://stock-data:5001/health",
            "http://sentiment:5002/health",
            "http://prediction:5003/health",
            "http://portfolio:5004/health",
            "http://technical:5005/health",
            "http://alert:5006/health",
        ]:
            respx.get(url).mock(return_value=httpx.Response(200, json={"status": "healthy"}))

        result = await mcp_client.health_check_all()
    assert all(v == "healthy" for v in result.values())
    assert "stock_data" in result
    assert "technical_analysis" in result


@pytest.mark.asyncio
async def test_health_check_partial_unreachable(mcp_client):
    with respx.mock:
        respx.get("http://stock-data:5001/health").mock(
            return_value=httpx.Response(200, json={"status": "healthy"})
        )
        for url in [
            "http://sentiment:5002/health",
            "http://prediction:5003/health",
            "http://portfolio:5004/health",
            "http://technical:5005/health",
            "http://alert:5006/health",
        ]:
            respx.get(url).mock(side_effect=httpx.ConnectError("refused"))

        result = await mcp_client.health_check_all()
    assert result["stock_data"] == "healthy"
    assert result["sentiment"] == "unreachable"


@pytest.mark.asyncio
async def test_call_tool_build_portfolio_routes_portfolio(mcp_client):
    with respx.mock:
        respx.post("http://portfolio:5004/tools/build_portfolio").mock(
            return_value=httpx.Response(200, json={"portfolio": [], "total": 0})
        )
        result = await mcp_client.call_tool("build_portfolio", {"symbols": ["RELIANCE", "TCS"]})
    assert "portfolio" in result


@pytest.mark.asyncio
async def test_call_tool_predict_stock_price_routes_prediction(mcp_client):
    with respx.mock:
        respx.post("http://prediction:5003/tools/predict_stock_price").mock(
            return_value=httpx.Response(200, json={"symbol": "NIFTY50", "prediction": 23000.0})
        )
        result = await mcp_client.call_tool("predict_stock_price", {"symbol": "NIFTY50"})
    assert result["prediction"] == 23000.0
