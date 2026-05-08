"""
Integration tests for the AI Orchestrator.
Tests the full request → Claude → MCP tool-use → response cycle
with Claude API and MCP HTTP calls mocked at the network boundary.
"""
import pytest
import httpx
import respx
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient


def _make_claude_response(text: str, stop_reason: str = "end_turn"):
    resp = MagicMock()
    resp.stop_reason = stop_reason
    block = MagicMock()
    block.type = "text"
    block.text = text
    resp.content = [block]
    return resp


def _make_tool_response(tool_name: str, tool_id: str, input_data: dict):
    resp = MagicMock()
    resp.stop_reason = "tool_use"
    block = MagicMock()
    block.type = "tool_use"
    block.id = tool_id
    block.name = tool_name
    block.input = input_data
    resp.content = [block]
    return resp


@pytest.fixture(scope="module")
def orchestrator_client():
    settings = MagicMock()
    settings.anthropic_api_key = "sk-ant-test"
    settings.claude_model = "claude-haiku-4-5-20251001"
    settings.mcp_stock_data_url = "http://stock-data:5001"
    settings.mcp_sentiment_url = "http://sentiment:5002"
    settings.mcp_prediction_url = "http://prediction:5003"
    settings.mcp_portfolio_url = "http://portfolio:5004"
    settings.mcp_technical_url = "http://technical:5005"
    settings.mcp_alert_url = "http://alert:5006"

    mock_anthropic = MagicMock()
    mock_mcp = AsyncMock()

    import sys
    sys.path.insert(0, "../../ai-orchestrator")

    with patch("main.settings", settings), \
         patch("main.claude_client", mock_anthropic), \
         patch("main.mcp", mock_mcp):
        from main import app
        with TestClient(app) as c:
            yield c, mock_anthropic, mock_mcp


# ── Health ────────────────────────────────────────────────────────

def test_health_check(orchestrator_client):
    client, _, _ = orchestrator_client
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"


# ── Analyze — simple end_turn ─────────────────────────────────────

def test_analyze_simple_response(orchestrator_client):
    client, mock_anthropic, _ = orchestrator_client
    mock_anthropic.messages.create.return_value = _make_claude_response(
        "RELIANCE is a strong buy. RSI=45, MACD bullish. Target: ₹3200."
    )

    r = client.post("/analyze", json={
        "user_id": "integ-user-1",
        "query": "Best Nifty 50 stocks",
        "country": "IN",
        "index": "NIFTY50",
        "investment_amount": 100000.0,
        "risk_profile": "MEDIUM",
        "time_horizon": "LONG_TERM",
        "strategy": "GROWTH",
        "preferred_sectors": [],
    })
    assert r.status_code == 200
    data = r.json()
    assert data["user_id"] == "integ-user-1"
    assert "RELIANCE" in data["analysis"]
    assert "latency_ms" in data
    assert data["tool_calls"] == []
    assert data["iterations"] == 1


# ── Analyze — tool_use then end_turn ─────────────────────────────

def test_analyze_with_tool_use_cycle(orchestrator_client):
    client, mock_anthropic, mock_mcp = orchestrator_client

    mock_anthropic.messages.create.side_effect = [
        _make_tool_response("get_technical_indicators", "tid_001", {"symbol": "TCS.NS"}),
        _make_claude_response("TCS shows RSI=52 — neutral zone. MACD is bullish. Recommend BUY."),
    ]
    mock_mcp.call_tool = AsyncMock(return_value={
        "symbol": "TCS",
        "rsi": 52.3,
        "macd": 12.5,
        "signals": {"overall": "BUY"},
    })

    r = client.post("/analyze", json={
        "user_id": "integ-user-2",
        "query": "Analyze TCS technical indicators",
        "country": "IN",
        "index": "NIFTY50",
        "investment_amount": 50000.0,
        "risk_profile": "LOW",
        "time_horizon": "SHORT_TERM",
        "strategy": "VALUE",
        "preferred_sectors": ["IT"],
    })
    assert r.status_code == 200
    data = r.json()
    assert data["iterations"] == 2
    assert len(data["tool_calls"]) == 1
    assert data["tool_calls"][0]["tool"] == "get_technical_indicators"
    assert "TCS" in data["analysis"]


# ── Analyze — multiple tool calls ────────────────────────────────

def test_analyze_multiple_tool_calls(orchestrator_client):
    client, mock_anthropic, mock_mcp = orchestrator_client

    mock_anthropic.messages.create.side_effect = [
        _make_tool_response("get_stock_price", "tid_002", {"symbol": "RELIANCE.NS"}),
        _make_tool_response("get_technical_indicators", "tid_003", {"symbol": "RELIANCE.NS"}),
        _make_claude_response("RELIANCE at ₹2850. RSI=45, bullish MACD. Strong buy with target ₹3200."),
    ]
    mock_mcp.call_tool = AsyncMock(side_effect=[
        {"symbol": "RELIANCE", "price": 2850.0, "change_percent": 1.2},
        {"symbol": "RELIANCE", "rsi": 45.0, "signals": {"overall": "BUY"}},
    ])

    r = client.post("/analyze", json={
        "user_id": "integ-user-3",
        "query": "Full analysis of Reliance",
        "country": "IN",
        "index": "NIFTY50",
        "investment_amount": 200000.0,
        "risk_profile": "HIGH",
        "time_horizon": "LONG_TERM",
        "strategy": "GROWTH",
        "preferred_sectors": ["Energy"],
    })
    assert r.status_code == 200
    data = r.json()
    assert data["iterations"] == 3
    assert len(data["tool_calls"]) == 2


# ── Chat ──────────────────────────────────────────────────────────

def test_chat_simple_message(orchestrator_client):
    client, mock_anthropic, _ = orchestrator_client
    mock_anthropic.messages.create.return_value = _make_claude_response(
        "TCS is trading at ₹3912. Strong fundamentals, IT sector leader."
    )

    r = client.post("/chat", json={
        "user_id": "chat-user-1",
        "message": "Is TCS a good buy?",
        "conversation_history": [],
    })
    assert r.status_code == 200
    data = r.json()
    assert "TCS" in data["response"]
    assert "latency_ms" in data
    assert "tool_calls_count" in data


def test_chat_preserves_conversation_context(orchestrator_client):
    client, mock_anthropic, _ = orchestrator_client
    mock_anthropic.messages.create.return_value = _make_claude_response(
        "Based on our previous discussion about TCS, Infosys also looks attractive."
    )

    r = client.post("/chat", json={
        "user_id": "chat-user-1",
        "message": "What about Infosys?",
        "conversation_history": [
            {"role": "user", "content": "Is TCS a good buy?"},
            {"role": "assistant", "content": "TCS looks bullish with strong fundamentals."},
        ],
    })
    assert r.status_code == 200
    # Verify history was forwarded to Claude
    call_args = mock_anthropic.messages.create.call_args
    messages = call_args[1]["messages"] if "messages" in call_args[1] else call_args[0][0]
    # There should be history + current message in the call
    assert len(messages) >= 3


# ── Metrics ───────────────────────────────────────────────────────

def test_metrics_endpoint(orchestrator_client):
    client, _, _ = orchestrator_client
    r = client.get("/metrics")
    assert r.status_code == 200
    assert b"orchestrator_requests_total" in r.content


# ── Validation ────────────────────────────────────────────────────

def test_analyze_missing_required_fields_returns_422(orchestrator_client):
    client, _, _ = orchestrator_client
    r = client.post("/analyze", json={"query": "test only"})
    assert r.status_code == 422


def test_chat_missing_message_returns_422(orchestrator_client):
    client, _, _ = orchestrator_client
    r = client.post("/chat", json={"user_id": "u1"})
    assert r.status_code == 422
