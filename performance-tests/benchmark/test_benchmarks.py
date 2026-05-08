"""
pytest-benchmark tests — micro-benchmarks for CPU-bound computations
in the technical analysis and MCP client routing layers.
"""
import sys
import pytest
import numpy as np
import pandas as pd

sys.path.insert(0, "../../mcp-servers/technical-analysis-server")
sys.path.insert(0, "../../ai-orchestrator")


def _make_prices(n: int = 500, seed: int = 42) -> pd.Series:
    np.random.seed(seed)
    return pd.Series(3000.0 + np.cumsum(np.random.normal(0, 10, n)))


# ── RSI ───────────────────────────────────────────────────────────

def test_bench_rsi_500_bars(benchmark):
    from main import compute_rsi
    prices = _make_prices(500)
    result = benchmark(compute_rsi, prices, 14)
    assert 0 <= result <= 100


def test_bench_rsi_2000_bars(benchmark):
    from main import compute_rsi
    prices = _make_prices(2000)
    result = benchmark(compute_rsi, prices, 14)
    assert 0 <= result <= 100


# ── MACD ──────────────────────────────────────────────────────────

def test_bench_macd_500_bars(benchmark):
    from main import compute_macd
    prices = _make_prices(500)
    macd, signal, hist = benchmark(compute_macd, prices)
    assert isinstance(macd, float)


def test_bench_macd_2000_bars(benchmark):
    from main import compute_macd
    prices = _make_prices(2000)
    macd, signal, hist = benchmark(compute_macd, prices)
    assert isinstance(macd, float)


# ── Bollinger Bands ───────────────────────────────────────────────

def test_bench_bollinger_500_bars(benchmark):
    from main import compute_bollinger
    prices = _make_prices(500)
    upper, mid, lower = benchmark(compute_bollinger, prices, 20)
    assert upper > lower


def test_bench_bollinger_2000_bars(benchmark):
    from main import compute_bollinger
    prices = _make_prices(2000)
    upper, mid, lower = benchmark(compute_bollinger, prices, 20)
    assert upper > lower


# ── Signal interpretation ─────────────────────────────────────────

def test_bench_interpret_signals(benchmark):
    from main import interpret_signals
    result = benchmark(interpret_signals, 45.0, 12.5, 10.0, 3050.0, 3000.0, 2950.0)
    assert result["overall"] in ("BUY", "SELL", "HOLD")


# ── MCP routing lookup ────────────────────────────────────────────

def test_bench_mcp_tool_routing_lookup(benchmark):
    from mcp_client import TOOL_ROUTING
    tools = list(TOOL_ROUTING.keys())

    def lookup_all():
        return [TOOL_ROUTING.get(t) for t in tools]

    result = benchmark(lookup_all)
    assert all(v is not None for v in result)


# ── Full RSI + MACD + Bollinger pipeline ──────────────────────────

def test_bench_full_ta_pipeline(benchmark):
    from main import compute_rsi, compute_macd, compute_bollinger, interpret_signals
    prices = _make_prices(500)

    def pipeline():
        rsi = compute_rsi(prices, 14)
        macd, signal, _ = compute_macd(prices)
        upper, mid, lower = compute_bollinger(prices, 20)
        sma_20 = float(prices.rolling(20).mean().iloc[-1])
        sma_50 = float(prices.rolling(50).mean().iloc[-1])
        return interpret_signals(rsi, macd, signal, float(prices.iloc[-1]), sma_20, sma_50)

    result = benchmark(pipeline)
    assert result["overall"] in ("BUY", "SELL", "HOLD")


# ── Performance thresholds ────────────────────────────────────────

def test_rsi_500_bars_under_10ms(benchmark):
    from main import compute_rsi
    prices = _make_prices(500)
    result = benchmark.pedantic(compute_rsi, args=(prices, 14), iterations=100, rounds=5)
    assert 0 <= result <= 100
    # benchmark.stats["mean"] is in seconds — assert < 10ms
    assert benchmark.stats["mean"] < 0.010, f"RSI too slow: {benchmark.stats['mean']*1000:.2f}ms"
