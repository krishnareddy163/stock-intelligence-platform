"""Integration test fixtures — spins up real FastAPI apps with mocked I/O boundaries."""
import json
import sys
import pytest
import pandas as pd
import numpy as np
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

sys.path.insert(0, "../../ai-orchestrator")
sys.path.insert(0, "../../mcp-servers/stock-data-server")
sys.path.insert(0, "../../mcp-servers/technical-analysis-server")


def _price_df(n=50, base=2800.0):
    np.random.seed(42)
    prices = base + np.cumsum(np.random.normal(0, 10, n))
    dates = pd.date_range("2024-01-01", periods=n, freq="B")
    return pd.DataFrame({
        "Open": prices - 3, "High": prices + 15,
        "Low": prices - 15, "Close": prices,
        "Volume": np.random.randint(500_000, 2_000_000, n),
    }, index=dates)


def _rich_df():
    return _price_df(n=250, base=3000.0)


@pytest.fixture(scope="session")
def mock_redis():
    r = AsyncMock()
    r.get = AsyncMock(return_value=None)
    r.setex = AsyncMock(return_value=True)
    return r


@pytest.fixture(scope="session")
def stock_data_client(mock_redis):
    ticker_mock = MagicMock()
    ticker_mock.history.return_value = _price_df()
    with patch("redis.asyncio.Redis", return_value=mock_redis), \
         patch("yfinance.Ticker", return_value=ticker_mock):
        import importlib, main as sd_main
        importlib.reload(sd_main)
        with TestClient(sd_main.app) as c:
            yield c


@pytest.fixture(scope="session")
def ta_client(mock_redis):
    ticker_mock = MagicMock()
    ticker_mock.history.return_value = _rich_df()
    with patch("redis.asyncio.Redis", return_value=mock_redis), \
         patch("yfinance.Ticker", return_value=ticker_mock):
        import importlib
        import sys as _sys
        _sys.path.insert(0, "../../mcp-servers/technical-analysis-server")
        import main as ta_main
        importlib.reload(ta_main)
        with TestClient(ta_main.app) as c:
            yield c
