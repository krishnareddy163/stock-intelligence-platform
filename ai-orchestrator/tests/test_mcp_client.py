"""Unit tests for McpClient — tool routing, timeouts, HTTP errors, health checks."""
import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock
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


def _ok_response(data: dict) -> MagicMock:
    r = MagicMock()
    r.raise_for_status.return_value = None
    r.json.return_value = data
    return r


def _error_response(status_code: int) -> MagicMock:
    inner = MagicMock()
    inner.status_code = status_code
    exc = httpx.HTTPStatusError(
        f"HTTP {status_code}",
        request=httpx.Request("POST", "http://test/"),
        response=inner,
    )
    r = MagicMock()
    r.raise_for_status.side_effect = exc
    return r


@pytest.mark.asyncio
async def test_call_tool_routes_stock_price(settings):
    client = McpClient(settings)
    client._client = MagicMock(
        post=AsyncMock(return_value=_ok_response({"symbol": "RELIANCE", "price": 2850.0}))
    )
    result = await client.call_tool("get_stock_price", {"symbol": "RELIANCE"})
    assert result["symbol"] == "RELIANCE"
    assert result["price"] == pytest.approx(2850.0)


@pytest.mark.asyncio
async def test_call_tool_routes_technical_indicators(settings):
    client = McpClient(settings)
    client._client = MagicMock(
        post=AsyncMock(return_value=_ok_response({"symbol": "TCS", "rsi": 55.2}))
    )
    result = await client.call_tool("get_technical_indicators", {"symbol": "TCS"})
    assert result["rsi"] == pytest.approx(55.2)


@pytest.mark.asyncio
async def test_call_tool_routes_sentiment(settings):
    client = McpClient(settings)
    client._client = MagicMock(
        post=AsyncMock(return_value=_ok_response({"symbol": "INFY", "sentiment": "POSITIVE"}))
    )
    result = await client.call_tool("get_news_sentiment", {"symbol": "INFY"})
    assert result["sentiment"] == "POSITIVE"


@pytest.mark.asyncio
async def test_call_tool_unknown_tool(settings):
    client = McpClient(settings)
    result = await client.call_tool("nonexistent_tool", {})
    assert "error" in result
    assert "Unknown tool" in result["error"]


@pytest.mark.asyncio
async def test_call_tool_timeout_returns_error(settings):
    client = McpClient(settings)
    client._client = MagicMock(
        post=AsyncMock(side_effect=httpx.TimeoutException("timed out"))
    )
    result = await client.call_tool("get_stock_price", {"symbol": "TCS"})
    assert result["error"] == "timeout"
    assert result["tool"] == "get_stock_price"


@pytest.mark.asyncio
async def test_call_tool_http_500_returns_error(settings):
    client = McpClient(settings)
    client._client = MagicMock(post=AsyncMock(return_value=_error_response(500)))
    result = await client.call_tool("get_stock_price", {"symbol": "HDFC"})
    assert "HTTP 500" in result["error"]


@pytest.mark.asyncio
async def test_call_tool_http_404_returns_error(settings):
    client = McpClient(settings)
    client._client = MagicMock(post=AsyncMock(return_value=_error_response(404)))
    result = await client.call_tool("get_stock_price", {"symbol": "UNKNOWN"})
    assert "HTTP 404" in result["error"]


@pytest.mark.asyncio
async def test_call_tool_connection_error_returns_error(settings):
    client = McpClient(settings)
    client._client = MagicMock(
        post=AsyncMock(side_effect=httpx.ConnectError("connection refused"))
    )
    result = await client.call_tool("get_stock_price", {"symbol": "WIPRO"})
    assert "error" in result


@pytest.mark.asyncio
async def test_health_check_all_healthy(settings):
    client = McpClient(settings)
    mock_response = MagicMock(status_code=200)
    client._client = MagicMock(get=AsyncMock(return_value=mock_response))

    result = await client.health_check_all()
    assert all(v == "healthy" for v in result.values())
    assert "stock_data" in result
    assert "technical_analysis" in result


@pytest.mark.asyncio
async def test_health_check_partial_unreachable(settings):
    client = McpClient(settings)
    mock_healthy = MagicMock(status_code=200)

    async def mock_get(url, timeout=None):
        if "stock-data" in url:
            return mock_healthy
        raise httpx.ConnectError("refused")

    client._client = MagicMock(get=mock_get)
    result = await client.health_check_all()
    assert result["stock_data"] == "healthy"
    assert result["sentiment"] == "unreachable"


@pytest.mark.asyncio
async def test_call_tool_build_portfolio_routes_portfolio(settings):
    client = McpClient(settings)
    client._client = MagicMock(
        post=AsyncMock(return_value=_ok_response({"portfolio": [], "total": 0}))
    )
    result = await client.call_tool("build_portfolio", {"symbols": ["RELIANCE", "TCS"]})
    assert "portfolio" in result


@pytest.mark.asyncio
async def test_call_tool_predict_stock_price_routes_prediction(settings):
    client = McpClient(settings)
    client._client = MagicMock(
        post=AsyncMock(return_value=_ok_response({"symbol": "NIFTY50", "prediction": 23000.0}))
    )
    result = await client.call_tool("predict_stock_price", {"symbol": "NIFTY50"})
    assert result["prediction"] == pytest.approx(23000.0)
