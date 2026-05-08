"""Unit tests for stock-data-server endpoints."""
import json
import pytest
import pandas as pd
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient


@pytest.fixture
def empty_df():
    return pd.DataFrame()


@pytest.fixture
def two_day_df():
    import pandas as pd
    dates = pd.date_range("2025-01-01", periods=2, freq="D")
    return pd.DataFrame(
        {
            "Open": [2800.0, 2820.0],
            "High": [2850.0, 2870.0],
            "Low": [2790.0, 2810.0],
            "Close": [2830.0, 2850.0],
            "Volume": [1_000_000, 1_200_000],
        },
        index=dates,
    )


@pytest.fixture
def historical_df():
    import pandas as pd
    dates = pd.date_range("2024-01-01", periods=10, freq="D")
    return pd.DataFrame(
        {
            "Open": [i * 100.0 for i in range(1, 11)],
            "High": [i * 100.0 + 10 for i in range(1, 11)],
            "Low": [i * 100.0 - 10 for i in range(1, 11)],
            "Close": [i * 100.0 + 5 for i in range(1, 11)],
            "Volume": [500_000] * 10,
        },
        index=dates,
    )


@pytest.fixture
def mock_redis():
    r = AsyncMock()
    r.get = AsyncMock(return_value=None)
    r.setex = AsyncMock(return_value=True)
    return r


def make_client(mock_redis, df):
    ticker_mock = MagicMock()
    ticker_mock.history.return_value = df
    return mock_redis, MagicMock(return_value=ticker_mock)


def test_health_endpoint(mock_redis, two_day_df):
    ticker_mock = MagicMock()
    ticker_mock.history.return_value = two_day_df
    with patch("main.aioredis.Redis", return_value=mock_redis), \
         patch("yfinance.Ticker", return_value=ticker_mock):
        from main import app
        with TestClient(app) as c:
            r = c.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"


def test_get_stock_price_success(mock_redis, two_day_df):
    ticker_mock = MagicMock()
    ticker_mock.history.return_value = two_day_df
    with patch("main.aioredis.Redis", return_value=mock_redis), \
         patch("yfinance.Ticker", return_value=ticker_mock):
        from main import app
        with TestClient(app) as c:
            r = c.post("/tools/get_stock_price", json={"symbol": "reliance"})
    assert r.status_code == 200
    data = r.json()
    assert data["symbol"] == "RELIANCE"
    assert data["price"] == 2850.0
    assert "change_percent" in data
    assert "volume" in data
    assert "timestamp" in data


def test_get_stock_price_cache_hit(mock_redis, two_day_df):
    cached = json.dumps({"symbol": "TCS", "price": 3900.0, "change_percent": 1.5,
                         "volume": 500000, "timestamp": "2025-01-01T00:00:00"})
    mock_redis.get = AsyncMock(return_value=cached)
    ticker_mock = MagicMock()
    ticker_mock.history.return_value = two_day_df
    with patch("main.aioredis.Redis", return_value=mock_redis), \
         patch("yfinance.Ticker", return_value=ticker_mock):
        from main import app
        with TestClient(app) as c:
            r = c.post("/tools/get_stock_price", json={"symbol": "TCS"})
    assert r.status_code == 200
    assert r.json()["price"] == 3900.0
    ticker_mock.history.assert_not_called()


def test_get_stock_price_not_found(mock_redis, empty_df):
    ticker_mock = MagicMock()
    ticker_mock.history.return_value = empty_df
    with patch("main.aioredis.Redis", return_value=mock_redis), \
         patch("yfinance.Ticker", return_value=ticker_mock):
        from main import app
        with TestClient(app) as c:
            r = c.post("/tools/get_stock_price", json={"symbol": "FAKEXYZ"})
    assert r.status_code == 404


def test_get_historical_data_success(mock_redis, historical_df):
    ticker_mock = MagicMock()
    ticker_mock.history.return_value = historical_df
    with patch("main.aioredis.Redis", return_value=mock_redis), \
         patch("yfinance.Ticker", return_value=ticker_mock):
        from main import app
        with TestClient(app) as c:
            r = c.post("/tools/get_historical_data", json={"symbol": "INFY", "days": 10})
    assert r.status_code == 200
    data = r.json()
    assert data["symbol"] == "INFY"
    assert len(data["data"]) == 10
    first = data["data"][0]
    assert "date" in first
    assert "open" in first and "close" in first


def test_get_historical_data_not_found(mock_redis, empty_df):
    ticker_mock = MagicMock()
    ticker_mock.history.return_value = empty_df
    with patch("main.aioredis.Redis", return_value=mock_redis), \
         patch("yfinance.Ticker", return_value=ticker_mock):
        from main import app
        with TestClient(app) as c:
            r = c.post("/tools/get_historical_data", json={"symbol": "BADTICKER"})
    assert r.status_code == 404


def test_get_market_index_data_nifty50(mock_redis, two_day_df):
    ticker_mock = MagicMock()
    ticker_mock.history.return_value = two_day_df
    with patch("main.aioredis.Redis", return_value=mock_redis), \
         patch("yfinance.Ticker", return_value=ticker_mock):
        from main import app
        with TestClient(app) as c:
            r = c.post("/tools/get_market_index_data", json={"index": "NIFTY50"})
    assert r.status_code == 200
    data = r.json()
    assert data["index"] == "NIFTY50"
    assert data["symbol"] == "^NSEI"
    assert "value" in data
    assert "change_percent" in data


def test_get_market_index_data_sensex(mock_redis, two_day_df):
    ticker_mock = MagicMock()
    ticker_mock.history.return_value = two_day_df
    with patch("main.aioredis.Redis", return_value=mock_redis), \
         patch("yfinance.Ticker", return_value=ticker_mock):
        from main import app
        with TestClient(app) as c:
            r = c.post("/tools/get_market_index_data", json={"index": "SENSEX"})
    assert r.status_code == 200
    assert r.json()["symbol"] == "^BSESN"


def test_get_market_index_data_cache_hit(mock_redis, two_day_df):
    cached = json.dumps({"index": "NASDAQ", "symbol": "^IXIC", "value": 18000.0,
                         "change_percent": -0.3, "timestamp": "2025-01-01T00:00:00"})
    mock_redis.get = AsyncMock(return_value=cached)
    ticker_mock = MagicMock()
    ticker_mock.history.return_value = two_day_df
    with patch("main.aioredis.Redis", return_value=mock_redis), \
         patch("yfinance.Ticker", return_value=ticker_mock):
        from main import app
        with TestClient(app) as c:
            r = c.post("/tools/get_market_index_data", json={"index": "NASDAQ"})
    assert r.status_code == 200
    assert r.json()["value"] == 18000.0
    ticker_mock.history.assert_not_called()


def test_get_market_index_data_not_found(mock_redis, empty_df):
    ticker_mock = MagicMock()
    ticker_mock.history.return_value = empty_df
    with patch("main.aioredis.Redis", return_value=mock_redis), \
         patch("yfinance.Ticker", return_value=ticker_mock):
        from main import app
        with TestClient(app) as c:
            r = c.post("/tools/get_market_index_data", json={"index": "UNKNOWN_IDX"})
    assert r.status_code == 404
