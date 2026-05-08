"""Unit tests for AI Orchestrator endpoints."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client with all external dependencies mocked."""
    mock_settings = MagicMock()
    mock_settings.anthropic_api_key = "sk-ant-test"
    mock_settings.claude_model = "claude-haiku-4-5-20251001"
    mock_settings.mcp_stock_data_url = "http://localhost:5001"
    mock_settings.mcp_sentiment_url = "http://localhost:5002"
    mock_settings.mcp_prediction_url = "http://localhost:5003"
    mock_settings.mcp_portfolio_url = "http://localhost:5004"
    mock_settings.mcp_technical_url = "http://localhost:5005"
    mock_settings.mcp_alert_url = "http://localhost:5006"

    mock_anthropic = MagicMock()
    mock_mcp = AsyncMock()

    with patch("main.settings", mock_settings), \
         patch("main.claude_client", mock_anthropic), \
         patch("main.mcp", mock_mcp):
        from main import app
        yield TestClient(app), mock_anthropic, mock_mcp


def test_health_endpoint(client):
    test_client, _, _ = client
    response = test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "model" in data


def test_analyze_calls_claude_and_returns_result(client):
    test_client, mock_anthropic, mock_mcp = client

    claude_response = MagicMock()
    claude_response.stop_reason = "end_turn"
    text_block = MagicMock()
    text_block.type = "text"
    text_block.text = "RELIANCE is a strong buy. Target: ₹3200."
    claude_response.content = [text_block]
    mock_anthropic.messages.create.return_value = claude_response

    payload = {
        "user_id": "user-123",
        "query": "Best Nifty 50 stocks",
        "country": "IN",
        "index": "NIFTY50",
        "investment_amount": 100000.0,
        "risk_profile": "MEDIUM",
        "time_horizon": "LONG_TERM",
        "strategy": "GROWTH",
        "preferred_sectors": [],
    }
    response = test_client.post("/analyze", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "user-123"
    assert "analysis" in data
    assert "tool_calls" in data
    assert "latency_ms" in data
    assert "RELIANCE" in data["analysis"]


def test_analyze_with_tool_calls(client):
    test_client, mock_anthropic, mock_mcp = client

    tool_use_response = MagicMock()
    tool_use_response.stop_reason = "tool_use"
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.id = "tool_abc123"
    tool_block.name = "get_market_index_data"
    tool_block.input = {"index": "NIFTY50"}
    tool_use_response.content = [tool_block]

    final_response = MagicMock()
    final_response.stop_reason = "end_turn"
    text_block = MagicMock()
    text_block.type = "text"
    text_block.text = "Based on NIFTY50 analysis, recommend RELIANCE."
    final_response.content = [text_block]

    mock_anthropic.messages.create.side_effect = [tool_use_response, final_response]
    mock_mcp.call_tool = AsyncMock(return_value={"index": "NIFTY50", "value": 22475.85})

    payload = {
        "user_id": "user-456",
        "query": "Analyze Nifty 50",
        "country": "IN",
        "index": "NIFTY50",
        "investment_amount": 50000.0,
        "risk_profile": "LOW",
        "time_horizon": "SHORT_TERM",
        "strategy": "VALUE",
        "preferred_sectors": ["IT", "Banking"],
    }
    response = test_client.post("/analyze", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert len(data["tool_calls"]) == 1
    assert data["tool_calls"][0]["tool"] == "get_market_index_data"
    assert data["iterations"] == 2


def test_analyze_missing_required_fields_returns_422(client):
    test_client, _, _ = client
    response = test_client.post("/analyze", json={"query": "test"})
    assert response.status_code == 422


def test_chat_returns_response(client):
    test_client, mock_anthropic, _ = client

    claude_response = MagicMock()
    claude_response.stop_reason = "end_turn"
    text_block = MagicMock()
    text_block.type = "text"
    text_block.text = "TCS is trading at ₹3912 with strong fundamentals."
    claude_response.content = [text_block]
    mock_anthropic.messages.create.return_value = claude_response

    payload = {
        "user_id": "user-789",
        "message": "Is TCS a good buy?",
        "conversation_history": [],
    }
    response = test_client.post("/chat", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "user-789"
    assert "response" in data
    assert "latency_ms" in data
    assert "tool_calls_count" in data


def test_chat_with_conversation_history(client):
    test_client, mock_anthropic, _ = client

    claude_response = MagicMock()
    claude_response.stop_reason = "end_turn"
    text_block = MagicMock()
    text_block.type = "text"
    text_block.text = "Given our previous discussion, INFY also looks attractive."
    claude_response.content = [text_block]
    mock_anthropic.messages.create.return_value = claude_response

    payload = {
        "user_id": "user-789",
        "message": "What about Infosys?",
        "conversation_history": [
            {"role": "user", "content": "Is TCS a good buy?"},
            {"role": "assistant", "content": "TCS looks bullish."},
        ],
    }
    response = test_client.post("/chat", json=payload)
    assert response.status_code == 200


def test_metrics_endpoint(client):
    test_client, _, _ = client
    response = test_client.get("/metrics")
    assert response.status_code == 200
    assert b"orchestrator_requests_total" in response.content
