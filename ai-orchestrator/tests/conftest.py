import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient


@pytest.fixture
def mock_settings():
    settings = MagicMock()
    settings.anthropic_api_key = "sk-ant-test-key"
    settings.claude_model = "claude-haiku-4-5-20251001"
    settings.mcp_stock_data_url = "http://stock-data-server:5001"
    settings.mcp_sentiment_url = "http://sentiment-server:5002"
    settings.mcp_prediction_url = "http://prediction-server:5003"
    settings.mcp_portfolio_url = "http://portfolio-server:5004"
    settings.mcp_technical_url = "http://technical-analysis-server:5005"
    settings.mcp_alert_url = "http://alert-server:5006"
    return settings


@pytest.fixture
def mock_mcp_client():
    client = AsyncMock()
    client.call_tool = AsyncMock(return_value={"status": "ok"})
    client.health_check_all = AsyncMock(return_value={
        "stock_data": "healthy",
        "sentiment": "healthy",
        "technical_analysis": "healthy",
        "portfolio": "healthy",
        "prediction": "healthy",
        "alert": "healthy",
    })
    return client


@pytest.fixture
def mock_claude_response():
    response = MagicMock()
    response.stop_reason = "end_turn"
    text_block = MagicMock()
    text_block.type = "text"
    text_block.text = "Analysis: RELIANCE is a strong buy with RSI at 45 and positive MACD crossover."
    response.content = [text_block]
    return response
