"""
Portfolio MCP Server
Portfolio construction via Modern Portfolio Theory (MPT) + risk-parity optimization
"""
import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime

import numpy as np
import pandas as pd
import redis.asyncio as aioredis
import yfinance as yf
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from scipy.optimize import minimize

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
redis_client: aioredis.Redis = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_client
    redis_client = aioredis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    yield
    await redis_client.aclose()


app = FastAPI(title="Portfolio MCP Server", version="1.0.0", lifespan=lifespan)


class PortfolioRequest(BaseModel):
    symbols: list[str]
    total_investment: float
    risk_profile: str = "MEDIUM"
    strategy: str = "GROWTH"


class RebalanceRequest(BaseModel):
    portfolio_id: str
    current_holdings: dict[str, float]  # symbol -> current_value
    target_allocations: dict[str, float]  # symbol -> target_pct


RISK_PARAMS = {
    "LOW": {"target_return": 0.08, "max_vol": 0.15, "rf_rate": 0.05},
    "MEDIUM": {"target_return": 0.15, "max_vol": 0.25, "rf_rate": 0.05},
    "HIGH": {"target_return": 0.25, "max_vol": 0.40, "rf_rate": 0.05},
}


def fetch_returns(symbols: list[str], period: str = "2y") -> pd.DataFrame:
    """Fetch daily returns for a list of symbols"""
    prices = {}
    for sym in symbols:
        try:
            ticker = yf.Ticker(sym)
            df = ticker.history(period=period)
            if not df.empty:
                prices[sym] = df["Close"]
        except Exception as e:
            logger.warning(f"Failed to fetch {sym}: {e}")

    if not prices:
        return pd.DataFrame()

    price_df = pd.DataFrame(prices).dropna()
    return price_df.pct_change().dropna()


def sharpe_ratio(weights: np.ndarray, returns: pd.DataFrame, rf: float = 0.05) -> float:
    port_ret = (returns.mean() * 252) @ weights
    port_vol = np.sqrt(weights @ (returns.cov() * 252).values @ weights)
    return -(port_ret - rf) / (port_vol + 1e-9)  # negative because we minimize


def optimize_portfolio(returns: pd.DataFrame, risk_profile: str) -> dict:
    """Mean-variance optimization for maximum Sharpe ratio"""
    n = len(returns.columns)
    params = RISK_PARAMS.get(risk_profile, RISK_PARAMS["MEDIUM"])

    constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1}]
    bounds = [(0.02, 0.40)] * n  # 2% min, 40% max per stock

    result = minimize(
        sharpe_ratio,
        x0=np.ones(n) / n,
        args=(returns, params["rf_rate"]),
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"maxiter": 1000},
    )

    weights = result.x if result.success else np.ones(n) / n
    weights = weights / weights.sum()  # renormalize

    port_ret = float((returns.mean() * 252) @ weights)
    cov_matrix = returns.cov().values * 252
    port_vol = float(np.sqrt(weights @ cov_matrix @ weights))
    sharpe = (port_ret - params["rf_rate"]) / (port_vol + 1e-9)

    return {
        "weights": dict(zip(returns.columns, [round(float(w), 4) for w in weights])),
        "expected_annual_return": round(port_ret * 100, 2),
        "annual_volatility": round(port_vol * 100, 2),
        "sharpe_ratio": round(sharpe, 3),
    }


def compute_holdings(symbols: list[str], weights: dict, total_investment: float) -> list[dict]:
    holdings = []
    for sym in symbols:
        weight = weights.get(sym, 0)
        if weight < 0.01:
            continue
        try:
            ticker = yf.Ticker(sym)
            price = float(ticker.history(period="1d")["Close"].iloc[-1])
            allocation = total_investment * weight
            quantity = int(allocation / price)
            holdings.append({
                "symbol": sym,
                "allocation_percent": round(weight * 100, 2),
                "allocation_amount": round(allocation, 2),
                "current_price": round(price, 2),
                "quantity": quantity,
                "actual_value": round(quantity * price, 2),
            })
        except Exception as e:
            logger.warning(f"Price fetch failed for {sym}: {e}")
    return sorted(holdings, key=lambda x: x["allocation_percent"], reverse=True)


@app.post("/tools/build_portfolio")
async def build_portfolio(req: PortfolioRequest):
    symbols = [s.upper() for s in req.symbols if s.strip()]
    if len(symbols) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 symbols")

    cache_key = f"portfolio:{'-'.join(sorted(symbols))}:{req.risk_profile}:{req.strategy}"
    cached = await redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    returns = fetch_returns(symbols)
    if returns.empty or returns.shape[1] < 2:
        raise HTTPException(status_code=422, detail="Insufficient historical data for optimization")

    # Keep only symbols we have data for
    valid_symbols = list(returns.columns)
    optimization = optimize_portfolio(returns, req.risk_profile)
    holdings = compute_holdings(valid_symbols, optimization["weights"], req.total_investment)

    result = {
        "portfolio": {
            "total_investment": req.total_investment,
            "risk_profile": req.risk_profile,
            "strategy": req.strategy,
            "stock_count": len(holdings),
            "expected_annual_return_pct": optimization["expected_annual_return"],
            "annual_volatility_pct": optimization["annual_volatility"],
            "sharpe_ratio": optimization["sharpe_ratio"],
        },
        "holdings": holdings,
        "optimization_method": "Mean-Variance (Sharpe Maximization)",
        "generated_at": datetime.utcnow().isoformat(),
    }

    await redis_client.setex(cache_key, 1800, json.dumps(result))
    logger.info(f"Portfolio built: {len(holdings)} stocks, Sharpe={optimization['sharpe_ratio']}")
    return result


@app.post("/tools/rebalance_portfolio")
async def rebalance_portfolio(req: RebalanceRequest):
    total_value = sum(req.current_holdings.values())
    trades = []

    for symbol, target_pct in req.target_allocations.items():
        current_value = req.current_holdings.get(symbol, 0)
        target_value = total_value * (target_pct / 100)
        drift = (current_value - target_value) / total_value * 100

        if abs(drift) > 2:  # rebalance if drift > 2%
            action = "SELL" if current_value > target_value else "BUY"
            trades.append({
                "symbol": symbol,
                "action": action,
                "amount": round(abs(current_value - target_value), 2),
                "current_pct": round(current_value / total_value * 100, 2),
                "target_pct": target_pct,
                "drift_pct": round(drift, 2),
            })

    return {
        "portfolio_id": req.portfolio_id,
        "total_value": total_value,
        "trades_required": len(trades),
        "rebalance_trades": sorted(trades, key=lambda x: abs(x["drift_pct"]), reverse=True),
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.post("/tools/simulate_portfolio")
async def simulate_portfolio(req: PortfolioRequest):
    """Monte Carlo simulation of portfolio outcomes"""
    symbols = [s.upper() for s in req.symbols]
    returns = fetch_returns(symbols, period="1y")
    if returns.empty:
        raise HTTPException(status_code=422, detail="No data available")

    n = len(returns.columns)
    weights = np.ones(n) / n

    mean_return = (returns.mean() * 252) @ weights
    cov_matrix = returns.cov().values * 252
    port_vol = np.sqrt(weights @ cov_matrix @ weights)

    # 1000 Monte Carlo paths over 1 year
    np.random.seed(42)
    simulations = 1000
    days = 252
    daily_returns = np.random.multivariate_normal(
        returns.mean().values, returns.cov().values, (simulations, days)
    )
    portfolio_paths = req.total_investment * np.cumprod(1 + daily_returns @ weights, axis=1)

    final_values = portfolio_paths[:, -1]
    percentiles = np.percentile(final_values, [5, 25, 50, 75, 95])

    return {
        "initial_investment": req.total_investment,
        "simulation_count": simulations,
        "outcomes": {
            "worst_5pct": round(float(percentiles[0]), 2),
            "lower_quartile": round(float(percentiles[1]), 2),
            "median": round(float(percentiles[2]), 2),
            "upper_quartile": round(float(percentiles[3]), 2),
            "best_5pct": round(float(percentiles[4]), 2),
        },
        "expected_return_pct": round(float(mean_return) * 100, 2),
        "annual_volatility_pct": round(float(port_vol) * 100, 2),
        "probability_of_profit": round(float(np.mean(final_values > req.total_investment)) * 100, 1),
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
