"""
X-Ray test configuration.
Tests are tagged with @pytest.mark.xray('STOCK-NNN') so results can be
imported into Jira X-Ray for traceability against requirements.

To push results to Jira X-Ray:
    pytest --jira-xray --cloud --client-id=$XRAY_CLIENT_ID --client-secret=$XRAY_SECRET
"""
import sys
import pytest
import httpx
import respx
from unittest.mock import MagicMock, AsyncMock

sys.path.insert(0, "../ai-orchestrator")
sys.path.insert(0, "../mcp-servers/stock-data-server")

ORCHESTRATOR_URL = "http://localhost:5000"
STOCK_DATA_URL   = "http://localhost:5001"
TA_URL           = "http://localhost:5005"
API_GATEWAY_URL  = "http://localhost:8080"


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "xray(key): marks a test with a Jira X-Ray test key for result import"
    )


@pytest.fixture(scope="session")
def settings():
    s = MagicMock()
    s.anthropic_api_key = "sk-ant-test"
    s.claude_model = "claude-haiku-4-5-20251001"
    s.mcp_stock_data_url = "http://stock-data:5001"
    s.mcp_sentiment_url  = "http://sentiment:5002"
    s.mcp_prediction_url = "http://prediction:5003"
    s.mcp_portfolio_url  = "http://portfolio:5004"
    s.mcp_technical_url  = "http://technical:5005"
    s.mcp_alert_url      = "http://alert:5006"
    return s
