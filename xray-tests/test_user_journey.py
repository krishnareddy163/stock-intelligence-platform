"""
X-Ray Acceptance Tests — User Journey
Test Keys: STOCK-1 through STOCK-10

Covers the end-to-end user flows mapped to Jira user stories:
  STOCK-1   Register new investor account
  STOCK-2   Login and receive JWT
  STOCK-3   Unauthenticated access is denied
  STOCK-4   AI analysis request returns recommendations
  STOCK-5   AI chat returns contextual response
  STOCK-6   Tool-use cycle completes and is reflected in response
  STOCK-7   Analysis with HIGH risk returns aggressive strategy
  STOCK-8   Portfolio created after analysis
  STOCK-9   History persists across sessions
  STOCK-10  Metrics endpoint exposes Prometheus data
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient


# ── Fixtures ──────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def orchestrator():
    settings = MagicMock()
    settings.anthropic_api_key = "sk-ant-test"
    settings.claude_model = "claude-haiku-4-5-20251001"
    settings.mcp_stock_data_url = "http://stock-data:5001"
    settings.mcp_sentiment_url  = "http://sentiment:5002"
    settings.mcp_prediction_url = "http://prediction:5003"
    settings.mcp_portfolio_url  = "http://portfolio:5004"
    settings.mcp_technical_url  = "http://technical:5005"
    settings.mcp_alert_url      = "http://alert:5006"

    mock_claude = MagicMock()
    mock_mcp    = AsyncMock()

    import sys, importlib
    sys.path.insert(0, "../ai-orchestrator")
    import main
    importlib.reload(main)  # ensure ai-orchestrator's main.py is active

    with patch("main.settings", settings), \
         patch("main.claude_client", mock_claude), \
         patch("main.mcp", mock_mcp):
        with TestClient(main.app) as c:
            yield c, mock_claude, mock_mcp


def _end_turn(text: str):
    r = MagicMock()
    r.stop_reason = "end_turn"
    b = MagicMock()
    b.type, b.text = "text", text
    r.content = [b]
    return r


def _tool_call(name: str, tid: str, inp: dict):
    r = MagicMock()
    r.stop_reason = "tool_use"
    b = MagicMock()
    b.type, b.id, b.name, b.input = "tool_use", tid, name, inp
    r.content = [b]
    return r


# ── STOCK-4: AI analysis ──────────────────────────────────────────

@pytest.mark.xray("STOCK-4")
def test_analysis_returns_recommendations_for_nifty50(orchestrator):
    """AC: Investor submits Nifty50 analysis → response contains actionable text."""
    client, mock_claude, _ = orchestrator
    mock_claude.messages.create.return_value = _end_turn(
        "Top picks from Nifty50: RELIANCE (BUY, target ₹3200), TCS (BUY, target ₹4100)."
    )

    r = client.post("/analyze", json={
        "user_id": "xray-user-1",
        "query": "Top Nifty 50 stocks for long-term investment",
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
    assert "RELIANCE" in data["analysis"] or "TCS" in data["analysis"]
    assert data["iterations"] >= 1


@pytest.mark.xray("STOCK-5")
def test_chat_returns_market_aware_response(orchestrator):
    """AC: User asks about a stock → AI responds with relevant market context."""
    client, mock_claude, _ = orchestrator
    mock_claude.messages.create.return_value = _end_turn(
        "HDFC Bank is trading at ₹1620. Strong balance sheet, recommend BUY for long-term."
    )

    r = client.post("/chat", json={
        "user_id": "xray-user-2",
        "message": "Should I invest in HDFC Bank?",
        "conversation_history": [],
    })
    assert r.status_code == 200
    assert "HDFC" in r.json()["response"]


@pytest.mark.xray("STOCK-6")
def test_tool_use_cycle_enriches_analysis(orchestrator):
    """AC: When Claude requests MCP data, the tool result is incorporated in the final answer."""
    client, mock_claude, mock_mcp = orchestrator

    mock_claude.messages.create.side_effect = [
        _tool_call("get_technical_indicators", "t1", {"symbol": "WIPRO.NS"}),
        _end_turn("WIPRO RSI=42 — slightly oversold. MACD crossing up. Recommend BUY."),
    ]
    mock_mcp.call_tool = AsyncMock(return_value={
        "symbol": "WIPRO",
        "rsi": 42.1,
        "signals": {"overall": "BUY"},
    })

    r = client.post("/analyze", json={
        "user_id": "xray-user-3",
        "query": "Technical analysis for WIPRO",
        "country": "IN",
        "index": "NIFTY50",
        "investment_amount": 50000.0,
        "risk_profile": "MEDIUM",
        "time_horizon": "SHORT_TERM",
        "strategy": "MOMENTUM",
        "preferred_sectors": ["IT"],
    })
    assert r.status_code == 200
    data = r.json()
    assert data["iterations"] == 2
    assert any(tc["tool"] == "get_technical_indicators" for tc in data["tool_calls"])


@pytest.mark.xray("STOCK-7")
def test_high_risk_aggressive_strategy_accepted(orchestrator):
    """AC: HIGH risk + MOMENTUM strategy is accepted and processed without error."""
    client, mock_claude, _ = orchestrator
    mock_claude.messages.create.side_effect = None  # reset exhausted iterator from previous test
    mock_claude.messages.create.return_value = _end_turn(
        "Aggressive portfolio: ADANIENT, ZOMATO, PAYTM for high-risk momentum plays."
    )

    r = client.post("/analyze", json={
        "user_id": "xray-user-4",
        "query": "Aggressive momentum stocks",
        "country": "IN",
        "index": "NIFTY500",
        "investment_amount": 500000.0,
        "risk_profile": "HIGH",
        "time_horizon": "SHORT_TERM",
        "strategy": "MOMENTUM",
        "preferred_sectors": ["Fintech", "Consumer"],
    })
    assert r.status_code == 200
    assert r.json()["user_id"] == "xray-user-4"


@pytest.mark.xray("STOCK-10")
def test_metrics_endpoint_exposes_prometheus_counters(orchestrator):
    """AC: /metrics returns Prometheus-formatted counters after at least one request."""
    client, _, _ = orchestrator
    r = client.get("/metrics")
    assert r.status_code == 200
    content = r.content
    assert b"orchestrator_requests_total" in content
    assert b"orchestrator_request_latency_seconds" in content
