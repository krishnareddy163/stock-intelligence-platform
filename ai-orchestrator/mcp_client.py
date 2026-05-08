"""
MCP Client — routes tool calls to the appropriate MCP server
"""
import asyncio
import logging
import time
import httpx

logger = logging.getLogger(__name__)

TOOL_ROUTING = {
    "get_stock_price": ("stock_data", 5001),
    "get_historical_data": ("stock_data", 5001),
    "get_market_index_data": ("stock_data", 5001),
    "get_technical_indicators": ("technical_analysis", 5005),
    "get_rsi": ("technical_analysis", 5005),
    "get_macd": ("technical_analysis", 5005),
    "get_moving_average": ("technical_analysis", 5005),
    "get_news_sentiment": ("sentiment", 5002),
    "get_social_sentiment": ("sentiment", 5002),
    "predict_stock_price": ("prediction", 5003),
    "predict_market_trend": ("prediction", 5003),
    "predict_volatility": ("prediction", 5003),
    "build_portfolio": ("portfolio", 5004),
    "rebalance_portfolio": ("portfolio", 5004),
    "simulate_portfolio": ("portfolio", 5004),
    "generate_buy_sell_signals": ("alert", 5006),
    "risk_alerts": ("alert", 5006),
}


class McpClient:
    def __init__(self, settings):
        self.settings = settings
        self.base_urls = {
            "stock_data": settings.mcp_stock_data_url,
            "sentiment": settings.mcp_sentiment_url,
            "prediction": settings.mcp_prediction_url,
            "portfolio": settings.mcp_portfolio_url,
            "technical_analysis": settings.mcp_technical_url,
            "alert": settings.mcp_alert_url,
        }
        self._client = httpx.AsyncClient(timeout=30.0)

    async def call_tool(self, tool_name: str, tool_input: dict) -> dict:
        routing = TOOL_ROUTING.get(tool_name)
        if not routing:
            return {"error": f"Unknown tool: {tool_name}"}

        server_key, _ = routing
        base_url = self.base_urls.get(server_key)
        if not base_url:
            return {"error": f"No URL configured for server: {server_key}"}

        url = f"{base_url}/tools/{tool_name}"
        start = time.time()

        try:
            resp = await self._client.post(url, json=tool_input)
            resp.raise_for_status()
            result = resp.json()
            logger.info(f"MCP {tool_name} → {server_key} [{int((time.time()-start)*1000)}ms]")
            return result
        except httpx.TimeoutException:
            logger.warning(f"MCP timeout: {tool_name}")
            return {"error": "timeout", "tool": tool_name}
        except httpx.HTTPStatusError as e:
            logger.error(f"MCP HTTP error {e.response.status_code}: {tool_name}")
            return {"error": f"HTTP {e.response.status_code}", "tool": tool_name}
        except Exception as e:
            logger.error(f"MCP call failed [{tool_name}]: {e}")
            return {"error": str(e), "tool": tool_name}

    async def health_check_all(self) -> dict[str, str]:
        """Check health of all MCP servers in parallel"""
        async def check(name, url):
            try:
                r = await self._client.get(f"{url}/health", timeout=5.0)
                return name, "healthy" if r.status_code == 200 else "degraded"
            except Exception:
                return name, "unreachable"

        tasks = [check(name, url) for name, url in self.base_urls.items()]
        results = await asyncio.gather(*tasks)
        return dict(results)

    async def close(self):
        await self._client.aclose()
