"""Shared fixtures for technical-analysis-server tests."""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient


@pytest.fixture
def mock_redis():
    r = AsyncMock()
    r.get = AsyncMock(return_value=None)
    r.setex = AsyncMock(return_value=True)
    return r


@pytest.fixture
def rich_ohlcv_df():
    """250 trading days of synthetic OHLCV data — enough for all indicators."""
    n = 250
    np.random.seed(42)
    prices = 3000.0 + np.cumsum(np.random.normal(0, 15, n))
    dates = pd.date_range("2024-01-01", periods=n, freq="B")
    return pd.DataFrame(
        {
            "Open": prices - 5,
            "High": prices + 20,
            "Low": prices - 20,
            "Close": prices,
            "Volume": np.random.randint(500_000, 2_000_000, n),
        },
        index=dates,
    )


@pytest.fixture
def short_df():
    """Only 30 rows — triggers 'insufficient data' for full TA."""
    n = 30
    np.random.seed(1)
    prices = 1000.0 + np.cumsum(np.random.normal(0, 5, n))
    dates = pd.date_range("2025-01-01", periods=n, freq="B")
    return pd.DataFrame(
        {"Open": prices, "High": prices + 5, "Low": prices - 5,
         "Close": prices, "Volume": [100_000] * n},
        index=dates,
    )
