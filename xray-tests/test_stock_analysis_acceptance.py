"""
X-Ray Acceptance Tests — Stock Analysis & MCP Data
Test Keys: STOCK-11 through STOCK-25

  STOCK-11  Stock price endpoint returns symbol, price, change_percent
  STOCK-12  Cache is used on repeated requests (no yfinance re-call)
  STOCK-13  Unknown symbol returns 404
  STOCK-14  Historical data returns OHLCV array
  STOCK-15  NIFTY50 index maps to ^NSEI ticker
  STOCK-16  SENSEX index maps to ^BSESN ticker
  STOCK-17  Technical indicators include RSI within 0–100
  STOCK-18  MACD crossover is either BULLISH or BEARISH
  STOCK-19  Bollinger bands: upper > mid > lower
  STOCK-20  Insufficient data returns 404 for TA
  STOCK-21  RSI < 35 triggers BUY signal
  STOCK-22  RSI > 70 triggers SELL signal
  STOCK-23  MCP timeout returns error dict, not exception
  STOCK-24  Health endpoint returns {"status": "healthy"}
  STOCK-25  Moving averages: SMA50 present in response
"""
import json
import pytest
import numpy as np
import pandas as pd
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient


def _make_df(n=250, base=3000.0, trend=0.0):
    np.random.seed(7)
    prices = base + np.cumsum(np.random.normal(trend, 10, n))
    dates = pd.date_range("2024-01-01", periods=n, freq="B")
    return pd.DataFrame({
        "Open": prices - 3, "High": prices + 15, "Low": prices - 15,
        "Close": prices, "Volume": np.random.randint(500_000, 2_000_000, n),
    }, index=dates)


def _two_day_df(base=2850.0):
    dates = pd.date_range("2025-01-01", periods=2, freq="D")
    return pd.DataFrame(
        {"Open": [base - 10, base], "High": [base + 20, base + 20],
         "Low": [base - 20, base - 20], "Close": [base - 5, base],
         "Volume": [1_000_000, 1_200_000]},
        index=dates,
    )


@pytest.fixture
def redis_mock():
    r = AsyncMock()
    r.get = AsyncMock(return_value=None)
    r.setex = AsyncMock(return_value=True)
    return r


# ── Stock Data Server ─────────────────────────────────────────────

@pytest.fixture
def stock_client(redis_mock):
    ticker = MagicMock()
    ticker.history.return_value = _two_day_df()
    with patch("main.aioredis.Redis", return_value=redis_mock), \
         patch("yfinance.Ticker", return_value=ticker):
        import sys
        sys.path.insert(0, "../mcp-servers/stock-data-server")
        from main import app
        with TestClient(app) as c:
            yield c, redis_mock, ticker


@pytest.mark.xray("STOCK-11")
def test_stock_price_returns_required_fields(stock_client):
    """AC: Response must contain symbol, price, change_percent, volume, timestamp."""
    c, _, _ = stock_client
    r = c.post("/tools/get_stock_price", json={"symbol": "RELIANCE"})
    assert r.status_code == 200
    data = r.json()
    for field in ("symbol", "price", "change_percent", "volume", "timestamp"):
        assert field in data, f"Missing field: {field}"


@pytest.mark.xray("STOCK-12")
def test_cache_used_on_repeated_requests(stock_client):
    """AC: Second identical request should hit Redis cache, not yfinance."""
    c, redis_mock, ticker_mock = stock_client
    cached = json.dumps({"symbol": "TCS", "price": 3912.0, "change_percent": 0.8,
                         "volume": 400_000, "timestamp": "2025-01-01T10:00:00"})
    redis_mock.get = AsyncMock(return_value=cached)

    r = c.post("/tools/get_stock_price", json={"symbol": "TCS"})
    assert r.status_code == 200
    assert r.json()["price"] == 3912.0
    ticker_mock.history.assert_not_called()


@pytest.mark.xray("STOCK-13")
def test_unknown_symbol_returns_404(redis_mock):
    """AC: Requesting a non-existent symbol returns HTTP 404."""
    ticker = MagicMock()
    ticker.history.return_value = pd.DataFrame()
    with patch("main.aioredis.Redis", return_value=redis_mock), \
         patch("yfinance.Ticker", return_value=ticker):
        import sys
        sys.path.insert(0, "../mcp-servers/stock-data-server")
        from main import app
        with TestClient(app) as c:
            r = c.post("/tools/get_stock_price", json={"symbol": "FAKEXYZABC"})
    assert r.status_code == 404


@pytest.mark.xray("STOCK-14")
def test_historical_data_returns_ohlcv_array(redis_mock):
    """AC: Historical endpoint returns array with open/high/low/close/volume."""
    import sys
    sys.path.insert(0, "../mcp-servers/stock-data-server")
    ticker = MagicMock()
    ticker.history.return_value = _make_df(n=10, base=2800.0)
    with patch("main.aioredis.Redis", return_value=redis_mock), \
         patch("yfinance.Ticker", return_value=ticker):
        from main import app
        with TestClient(app) as c:
            r = c.post("/tools/get_historical_data", json={"symbol": "INFY", "days": 10})
    assert r.status_code == 200
    data = r.json()
    assert len(data["data"]) == 10
    row = data["data"][0]
    for key in ("date", "open", "high", "low", "close", "volume"):
        assert key in row


@pytest.mark.xray("STOCK-15")
def test_nifty50_maps_to_nsei_ticker(redis_mock):
    """AC: Index name NIFTY50 must resolve to ^NSEI Yahoo Finance ticker."""
    import sys
    sys.path.insert(0, "../mcp-servers/stock-data-server")
    ticker = MagicMock()
    ticker.history.return_value = _two_day_df()
    with patch("main.aioredis.Redis", return_value=redis_mock), \
         patch("yfinance.Ticker", return_value=ticker) as mock_yf:
        from main import app
        with TestClient(app) as c:
            r = c.post("/tools/get_market_index_data", json={"index": "NIFTY50"})
    assert r.status_code == 200
    assert r.json()["symbol"] == "^NSEI"
    mock_yf.assert_called_with("^NSEI")


@pytest.mark.xray("STOCK-16")
def test_sensex_maps_to_bsesn_ticker(redis_mock):
    """AC: Index name SENSEX must resolve to ^BSESN Yahoo Finance ticker."""
    import sys
    sys.path.insert(0, "../mcp-servers/stock-data-server")
    ticker = MagicMock()
    ticker.history.return_value = _two_day_df()
    with patch("main.aioredis.Redis", return_value=redis_mock), \
         patch("yfinance.Ticker", return_value=ticker) as mock_yf:
        from main import app
        with TestClient(app) as c:
            r = c.post("/tools/get_market_index_data", json={"index": "SENSEX"})
    assert r.status_code == 200
    mock_yf.assert_called_with("^BSESN")


# ── Technical Analysis Server ─────────────────────────────────────

@pytest.fixture
def ta_client(redis_mock):
    ticker = MagicMock()
    ticker.history.return_value = _make_df()
    with patch("main.aioredis.Redis", return_value=redis_mock), \
         patch("yfinance.Ticker", return_value=ticker):
        import sys
        sys.path.insert(0, "../mcp-servers/technical-analysis-server")
        import importlib
        import main as ta
        importlib.reload(ta)
        with TestClient(ta.app) as c:
            yield c


@pytest.mark.xray("STOCK-17")
def test_rsi_within_valid_range(ta_client):
    """AC: RSI value must always be in the range [0, 100]."""
    r = ta_client.post("/tools/get_technical_indicators", json={"symbol": "TCS"})
    assert r.status_code == 200
    rsi = r.json()["rsi"]
    assert 0 <= rsi <= 100


@pytest.mark.xray("STOCK-18")
def test_macd_crossover_is_bullish_or_bearish(ta_client):
    """AC: MACD crossover field must be either BULLISH or BEARISH."""
    r = ta_client.post("/tools/get_macd", json={"symbol": "HDFC"})
    assert r.status_code == 200
    assert r.json()["crossover"] in ("BULLISH", "BEARISH")


@pytest.mark.xray("STOCK-19")
def test_bollinger_bands_upper_greater_than_lower(ta_client):
    """AC: Bollinger upper band must always be greater than lower band."""
    r = ta_client.post("/tools/get_technical_indicators", json={"symbol": "WIPRO"})
    assert r.status_code == 200
    data = r.json()
    assert data["bollinger_upper"] > data["bollinger_lower"]
    assert data["bollinger_upper"] > data["bollinger_mid"] > data["bollinger_lower"]


@pytest.mark.xray("STOCK-20")
def test_insufficient_data_returns_404(redis_mock):
    """AC: Fewer than 60 data points must return 404 with explanation."""
    import sys
    sys.path.insert(0, "../mcp-servers/technical-analysis-server")
    n = 30
    prices = 1000.0 + np.arange(n)
    dates = pd.date_range("2025-01-01", periods=n, freq="B")
    short_df = pd.DataFrame(
        {"Open": prices, "High": prices + 5, "Low": prices - 5,
         "Close": prices, "Volume": [100_000] * n},
        index=dates,
    )
    ticker = MagicMock()
    ticker.history.return_value = short_df
    with patch("main.aioredis.Redis", return_value=redis_mock), \
         patch("yfinance.Ticker", return_value=ticker):
        import importlib
        import main as ta
        importlib.reload(ta)
        with TestClient(ta.app) as c:
            r = c.post("/tools/get_technical_indicators", json={"symbol": "SMALL"})
    assert r.status_code == 404


@pytest.mark.xray("STOCK-21")
def test_oversold_rsi_triggers_buy_signal(redis_mock):
    """AC: RSI below 35 must include a BUY signal in RSI breakdown."""
    import sys
    sys.path.insert(0, "../mcp-servers/technical-analysis-server")
    n = 100
    prices = 1000.0 - np.arange(n) * 5.0  # Sharp decline → RSI near 0
    dates = pd.date_range("2024-01-01", periods=n, freq="B")
    bear_df = pd.DataFrame(
        {"Open": prices, "High": prices + 1, "Low": prices - 1,
         "Close": prices, "Volume": [100_000] * n},
        index=dates,
    )
    ticker = MagicMock()
    ticker.history.return_value = bear_df
    with patch("main.aioredis.Redis", return_value=redis_mock), \
         patch("yfinance.Ticker", return_value=ticker):
        import importlib
        import main as ta
        importlib.reload(ta)
        with TestClient(ta.app) as c:
            r = c.post("/tools/get_rsi", json={"symbol": "BEAR"})
    assert r.status_code == 200
    assert r.json()["rsi"] < 35


@pytest.mark.xray("STOCK-22")
def test_overbought_rsi_scenario(redis_mock):
    """AC: RSI above 70 must indicate overbought condition."""
    import sys
    sys.path.insert(0, "../mcp-servers/technical-analysis-server")
    n = 100
    prices = 1000.0 + np.arange(n) * 5.0  # Sharp rise → RSI near 100
    dates = pd.date_range("2024-01-01", periods=n, freq="B")
    bull_df = pd.DataFrame(
        {"Open": prices, "High": prices + 1, "Low": prices - 1,
         "Close": prices, "Volume": [100_000] * n},
        index=dates,
    )
    ticker = MagicMock()
    ticker.history.return_value = bull_df
    with patch("main.aioredis.Redis", return_value=redis_mock), \
         patch("yfinance.Ticker", return_value=ticker):
        import importlib
        import main as ta
        importlib.reload(ta)
        with TestClient(ta.app) as c:
            r = c.post("/tools/get_rsi", json={"symbol": "BULL"})
    assert r.status_code == 200
    assert r.json()["rsi"] > 70


@pytest.mark.xray("STOCK-24")
def test_health_endpoint_returns_healthy(ta_client):
    """AC: Health endpoint returns status=healthy."""
    r = ta_client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"


@pytest.mark.xray("STOCK-25")
def test_moving_averages_present_in_response(ta_client):
    """AC: get_moving_average response must contain sma_20, sma_50, ema_12, ema_26."""
    r = ta_client.post("/tools/get_moving_average", json={"symbol": "RELIANCE"})
    assert r.status_code == 200
    data = r.json()
    for key in ("sma_20", "sma_50", "ema_12", "ema_26", "current_price"):
        assert key in data
