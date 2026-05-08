"""Unit tests for technical-analysis-server endpoints."""
import json
import pytest
import pandas as pd
import numpy as np
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient


def _rich_df(n=250, seed=42):
    np.random.seed(seed)
    prices = 3000.0 + np.cumsum(np.random.normal(0, 15, n))
    dates = pd.date_range("2024-01-01", periods=n, freq="B")
    return pd.DataFrame(
        {"Open": prices - 5, "High": prices + 20, "Low": prices - 20,
         "Close": prices, "Volume": np.random.randint(500_000, 2_000_000, n)},
        index=dates,
    )


def _empty_df():
    return pd.DataFrame()


def _short_df(n=30):
    np.random.seed(1)
    prices = 1000.0 + np.cumsum(np.random.normal(0, 5, n))
    dates = pd.date_range("2025-01-01", periods=n, freq="B")
    return pd.DataFrame(
        {"Open": prices, "High": prices + 5, "Low": prices - 5,
         "Close": prices, "Volume": [100_000] * n},
        index=dates,
    )


@pytest.fixture
def mock_redis():
    r = AsyncMock()
    r.get = AsyncMock(return_value=None)
    r.setex = AsyncMock(return_value=True)
    return r


def _build_client(mock_redis, df):
    ticker_mock = MagicMock()
    ticker_mock.history.return_value = df
    mock_yf = MagicMock(return_value=ticker_mock)
    return mock_yf


def test_health_endpoint(mock_redis):
    yf_mock = _build_client(mock_redis, _rich_df())
    with patch("main.aioredis.Redis", return_value=mock_redis), patch("yfinance.Ticker", yf_mock):
        from main import app
        with TestClient(app) as c:
            r = c.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"


def test_get_technical_indicators_success(mock_redis):
    yf_mock = _build_client(mock_redis, _rich_df())
    with patch("main.aioredis.Redis", return_value=mock_redis), patch("yfinance.Ticker", yf_mock):
        from main import app
        with TestClient(app) as c:
            r = c.post("/tools/get_technical_indicators", json={"symbol": "RELIANCE"})
    assert r.status_code == 200
    data = r.json()
    assert data["symbol"] == "RELIANCE"
    assert "rsi" in data
    assert 0 <= data["rsi"] <= 100
    assert "macd" in data
    assert "sma_20" in data
    assert "sma_50" in data
    assert "bollinger_upper" in data
    assert "bollinger_lower" in data
    assert "signals" in data
    assert data["signals"]["overall"] in ("BUY", "SELL", "HOLD")


def test_get_technical_indicators_cache_hit(mock_redis):
    cached_result = {
        "symbol": "TCS", "rsi": 62.5, "macd": 15.3, "macd_signal": 12.0,
        "macd_histogram": 3.3, "sma_20": 3850.0, "sma_50": 3800.0,
        "signals": {"overall": "BUY", "breakdown": []},
        "timestamp": "2025-01-01T00:00:00",
    }
    mock_redis.get = AsyncMock(return_value=json.dumps(cached_result))
    yf_mock = _build_client(mock_redis, _rich_df())
    with patch("main.aioredis.Redis", return_value=mock_redis), patch("yfinance.Ticker", yf_mock):
        from main import app
        with TestClient(app) as c:
            r = c.post("/tools/get_technical_indicators", json={"symbol": "TCS"})
    assert r.status_code == 200
    assert r.json()["rsi"] == 62.5
    yf_mock.return_value.history.assert_not_called()


def test_get_technical_indicators_insufficient_data(mock_redis):
    yf_mock = _build_client(mock_redis, _short_df())
    with patch("main.aioredis.Redis", return_value=mock_redis), patch("yfinance.Ticker", yf_mock):
        from main import app
        with TestClient(app) as c:
            r = c.post("/tools/get_technical_indicators", json={"symbol": "SMALL"})
    assert r.status_code == 404


def test_get_technical_indicators_not_found(mock_redis):
    yf_mock = _build_client(mock_redis, _empty_df())
    with patch("main.aioredis.Redis", return_value=mock_redis), patch("yfinance.Ticker", yf_mock):
        from main import app
        with TestClient(app) as c:
            r = c.post("/tools/get_technical_indicators", json={"symbol": "FAKEXYZ"})
    assert r.status_code == 404


def test_get_rsi_success(mock_redis):
    yf_mock = _build_client(mock_redis, _rich_df())
    with patch("main.aioredis.Redis", return_value=mock_redis), patch("yfinance.Ticker", yf_mock):
        from main import app
        with TestClient(app) as c:
            r = c.post("/tools/get_rsi", json={"symbol": "WIPRO", "period": 14})
    assert r.status_code == 200
    data = r.json()
    assert data["symbol"] == "WIPRO"
    assert 0 <= data["rsi"] <= 100
    assert data["period"] == 14


def test_get_rsi_not_found(mock_redis):
    yf_mock = _build_client(mock_redis, _empty_df())
    with patch("main.aioredis.Redis", return_value=mock_redis), patch("yfinance.Ticker", yf_mock):
        from main import app
        with TestClient(app) as c:
            r = c.post("/tools/get_rsi", json={"symbol": "FAKE"})
    assert r.status_code == 404


def test_get_macd_success(mock_redis):
    yf_mock = _build_client(mock_redis, _rich_df())
    with patch("main.aioredis.Redis", return_value=mock_redis), patch("yfinance.Ticker", yf_mock):
        from main import app
        with TestClient(app) as c:
            r = c.post("/tools/get_macd", json={"symbol": "HDFCBANK"})
    assert r.status_code == 200
    data = r.json()
    assert "macd" in data
    assert "signal" in data
    assert "histogram" in data
    assert data["crossover"] in ("BULLISH", "BEARISH")


def test_get_moving_average_success(mock_redis):
    yf_mock = _build_client(mock_redis, _rich_df())
    with patch("main.aioredis.Redis", return_value=mock_redis), patch("yfinance.Ticker", yf_mock):
        from main import app
        with TestClient(app) as c:
            r = c.post("/tools/get_moving_average", json={"symbol": "INFY"})
    assert r.status_code == 200
    data = r.json()
    assert "sma_20" in data
    assert "sma_50" in data
    assert "ema_12" in data
    assert "ema_26" in data
    assert "current_price" in data


def test_rsi_oversold_signal(mock_redis):
    """Force an oversold RSI by using steadily declining prices."""
    n = 100
    prices = 1000.0 - np.arange(n) * 5.0  # sharp decline → RSI near 0
    dates = pd.date_range("2024-01-01", periods=n, freq="B")
    df = pd.DataFrame(
        {"Open": prices, "High": prices + 1, "Low": prices - 1,
         "Close": prices, "Volume": [100_000] * n},
        index=dates,
    )
    yf_mock = _build_client(mock_redis, df)
    with patch("main.aioredis.Redis", return_value=mock_redis), patch("yfinance.Ticker", yf_mock):
        from main import app
        with TestClient(app) as c:
            r = c.post("/tools/get_rsi", json={"symbol": "BEAR"})
    assert r.status_code == 200
    assert r.json()["rsi"] < 35
