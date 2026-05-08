"""
Locust performance tests for the Stock Intelligence Platform.

Run:
    locust -f locustfile.py --host=http://localhost:8000 --users=50 --spawn-rate=5

Targets:
    - AI Orchestrator  :8000  — heavy users
    - Stock Data MCP   :5001  — data fetchers
    - Technical MCP    :5005  — signal checkers
"""
import random
import json
from locust import HttpUser, task, between, events
from locust.contrib.fasthttp import FastHttpUser


NIFTY50_SYMBOLS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFOSYS.NS", "ICICIBANK.NS",
    "HINDUNILVR.NS", "ITC.NS", "SBIN.NS", "BHARTIARTL.NS", "KOTAKBANK.NS",
    "WIPRO.NS", "AXISBANK.NS", "LTIM.NS", "HCLTECH.NS", "MARUTI.NS",
]

INDICES = ["NIFTY50", "SENSEX", "NASDAQ", "SP500"]

RISK_PROFILES = ["LOW", "MEDIUM", "HIGH"]
STRATEGIES = ["GROWTH", "VALUE", "DIVIDEND", "MOMENTUM"]
TIME_HORIZONS = ["SHORT_TERM", "MEDIUM_TERM", "LONG_TERM"]
SECTORS = ["IT", "Banking", "FMCG", "Auto", "Pharma", "Energy", "Metal"]


class OrchestratorUser(HttpUser):
    """Simulates a retail investor hitting the AI Orchestrator API."""

    wait_time = between(1, 4)
    host = "http://localhost:8000"
    weight = 3

    def on_start(self):
        self.user_id = f"perf-user-{random.randint(1000, 9999)}"
        self.conversation_history = []

    @task(5)
    def analyze_stocks(self):
        payload = {
            "user_id": self.user_id,
            "query": f"Best stocks from {random.choice(INDICES)}?",
            "country": "IN",
            "index": random.choice(INDICES),
            "investment_amount": random.choice([50000, 100000, 500000, 1000000]),
            "risk_profile": random.choice(RISK_PROFILES),
            "time_horizon": random.choice(TIME_HORIZONS),
            "strategy": random.choice(STRATEGIES),
            "preferred_sectors": random.sample(SECTORS, k=random.randint(0, 3)),
        }
        with self.client.post(
            "/analyze",
            json=payload,
            catch_response=True,
            name="/analyze",
        ) as resp:
            if resp.status_code == 200:
                data = resp.json()
                if "analysis" not in data:
                    resp.failure("Missing analysis field in response")
            elif resp.status_code == 422:
                resp.failure(f"Validation error: {resp.text[:200]}")
            else:
                resp.failure(f"Unexpected status {resp.status_code}")

    @task(3)
    def chat_query(self):
        symbol = random.choice(NIFTY50_SYMBOLS)
        payload = {
            "user_id": self.user_id,
            "message": f"Should I buy {symbol} now?",
            "conversation_history": self.conversation_history[-4:],
        }
        with self.client.post(
            "/chat",
            json=payload,
            catch_response=True,
            name="/chat",
        ) as resp:
            if resp.status_code == 200:
                data = resp.json()
                if "response" in data:
                    self.conversation_history.append({"role": "user", "content": payload["message"]})
                    self.conversation_history.append({"role": "assistant", "content": data["response"]})
                    if len(self.conversation_history) > 20:
                        self.conversation_history = self.conversation_history[-10:]
                else:
                    resp.failure("Missing response field")
            else:
                resp.failure(f"Chat failed: {resp.status_code}")

    @task(2)
    def health_check(self):
        self.client.get("/health", name="/health")

    @task(1)
    def metrics(self):
        self.client.get("/metrics", name="/metrics")


class StockDataUser(HttpUser):
    """Simulates direct calls to the Stock Data MCP server."""

    wait_time = between(0.5, 2)
    host = "http://localhost:5001"
    weight = 2

    @task(4)
    def get_stock_price(self):
        symbol = random.choice(NIFTY50_SYMBOLS)
        with self.client.post(
            "/tools/get_stock_price",
            json={"symbol": symbol},
            catch_response=True,
            name="/tools/get_stock_price",
        ) as resp:
            if resp.status_code not in (200, 404):
                resp.failure(f"Unexpected {resp.status_code}")

    @task(2)
    def get_market_index(self):
        with self.client.post(
            "/tools/get_market_index_data",
            json={"index": random.choice(INDICES)},
            catch_response=True,
            name="/tools/get_market_index_data",
        ) as resp:
            if resp.status_code not in (200, 404):
                resp.failure(f"Unexpected {resp.status_code}")

    @task(1)
    def get_historical(self):
        symbol = random.choice(NIFTY50_SYMBOLS)
        days = random.choice([30, 90, 180, 365])
        with self.client.post(
            "/tools/get_historical_data",
            json={"symbol": symbol, "days": days},
            catch_response=True,
            name="/tools/get_historical_data",
        ) as resp:
            if resp.status_code not in (200, 404):
                resp.failure(f"Unexpected {resp.status_code}")

    @task(1)
    def health(self):
        self.client.get("/health", name="/health")


class TechnicalAnalysisUser(HttpUser):
    """Simulates calls to the Technical Analysis MCP server."""

    wait_time = between(1, 3)
    host = "http://localhost:5005"
    weight = 1

    @task(4)
    def get_technical_indicators(self):
        symbol = random.choice(NIFTY50_SYMBOLS)
        with self.client.post(
            "/tools/get_technical_indicators",
            json={"symbol": symbol, "period": 14},
            catch_response=True,
            name="/tools/get_technical_indicators",
        ) as resp:
            if resp.status_code == 200:
                data = resp.json()
                if "rsi" not in data:
                    resp.failure("Missing rsi in response")
            elif resp.status_code not in (404, 500):
                resp.failure(f"Unexpected {resp.status_code}")

    @task(2)
    def get_rsi(self):
        symbol = random.choice(NIFTY50_SYMBOLS)
        with self.client.post(
            "/tools/get_rsi",
            json={"symbol": symbol},
            catch_response=True,
            name="/tools/get_rsi",
        ) as resp:
            if resp.status_code not in (200, 404):
                resp.failure(f"Unexpected {resp.status_code}")

    @task(1)
    def get_macd(self):
        symbol = random.choice(NIFTY50_SYMBOLS)
        with self.client.post(
            "/tools/get_macd",
            json={"symbol": symbol},
            catch_response=True,
            name="/tools/get_macd",
        ) as resp:
            if resp.status_code not in (200, 404):
                resp.failure(f"Unexpected {resp.status_code}")

    @task(1)
    def health(self):
        self.client.get("/health", name="/health")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print("\n[StockIQ Perf] Starting load test — targeting AI Orchestrator + MCP servers")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    stats = environment.stats.total
    print(f"\n[StockIQ Perf] Done — "
          f"RPS={stats.current_rps:.1f}, "
          f"p95={stats.get_response_time_percentile(0.95):.0f}ms, "
          f"failures={stats.num_failures}")
