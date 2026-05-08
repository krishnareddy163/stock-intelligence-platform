"""Shared fixtures for stock-data-server tests."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient


@pytest.fixture
def mock_redis():
    r = AsyncMock()
    r.get = AsyncMock(return_value=None)
    r.setex = AsyncMock(return_value=True)
    return r


@pytest.fixture
def mock_ticker_data():
    """Returns a minimal yfinance-like DataFrame mock with 2 rows."""
    import pandas as pd
    dates = pd.date_range("2025-01-01", periods=2, freq="D")
    df = pd.DataFrame(
        {
            "Open": [2800.0, 2820.0],
            "High": [2850.0, 2870.0],
            "Low": [2790.0, 2810.0],
            "Close": [2830.0, 2850.0],
            "Volume": [1_000_000, 1_200_000],
        },
        index=dates,
    )
    return df


@pytest.fixture
def client(mock_redis, mock_ticker_data):
    with patch("main.redis_client", mock_redis), \
         patch("yfinance.Ticker") as mock_yf:
        ticker_mock = MagicMock()
        ticker_mock.history.return_value = mock_ticker_data
        mock_yf.return_value = ticker_mock

        from main import app
        with TestClient(app) as c:
            yield c, mock_redis, mock_yf
