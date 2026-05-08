"""
Alert MCP Server
Buy/sell signal generation and risk alerts using multi-factor scoring
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


app = FastAPI(title="Alert MCP Server", version="1.0.0", lifespan=lifespan)


class SignalRequest(BaseModel):
    symbols: list[str]
    risk_profile: str = "MEDIUM"


class RiskAlertRequest(BaseModel):
    symbol: str
    position_size: float = 0.0


def compute_signal_score(df: pd.DataFrame) -> dict:
    """Multi-factor signal: RSI + MACD + trend + volume confirmation"""
    close = df["Close"]
    volume = df["Volume"]

    # RSI
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rsi = float(100 - 100 / (1 + gain.iloc[-1] / (loss.iloc[-1] + 1e-9)))

    # MACD
    ema12 = close.ewm(span=12).mean()
    ema26 = close.ewm(span=26).mean()
    macd = float((ema12 - ema26).iloc[-1])
    signal_line = float((ema12 - ema26).ewm(span=9).mean().iloc[-1])

    # Trend (SMA 20 vs 50)
    sma20 = float(close.rolling(20).mean().iloc[-1])
    sma50 = float(close.rolling(50).mean().iloc[-1])
    current_price = float(close.iloc[-1])

    # Volume confirmation
    avg_vol = float(volume.rolling(20).mean().iloc[-1])
    current_vol = float(volume.iloc[-1])
    vol_confirm = current_vol > avg_vol * 1.2

    # Score components (each -1 to +1)
    score = 0
    reasons = []

    if rsi < 35:
        score += 2; reasons.append(f"RSI {rsi:.1f} — deeply oversold, strong buy signal")
    elif rsi < 45:
        score += 1; reasons.append(f"RSI {rsi:.1f} — slightly oversold")
    elif rsi > 65:
        score -= 1; reasons.append(f"RSI {rsi:.1f} — approaching overbought")
    elif rsi > 75:
        score -= 2; reasons.append(f"RSI {rsi:.1f} — overbought, consider selling")

    if macd > signal_line:
        score += 1; reasons.append("MACD bullish crossover — upward momentum")
    else:
        score -= 1; reasons.append("MACD bearish — downward momentum")

    if current_price > sma20 > sma50:
        score += 2; reasons.append("Price above SMA20 > SMA50 — strong uptrend")
    elif current_price < sma20 < sma50:
        score -= 2; reasons.append("Price below SMA20 < SMA50 — downtrend")

    if vol_confirm and score > 0:
        score += 1; reasons.append("High volume confirms upward move")
    elif vol_confirm and score < 0:
        score -= 1; reasons.append("High volume confirms downward move")

    # Convert score to action
    if score >= 3:
        action = "STRONG_BUY"
        strength = min(score / 6.0, 1.0)
    elif score >= 1:
        action = "BUY"
        strength = score / 6.0
    elif score <= -3:
        action = "STRONG_SELL"
        strength = min(abs(score) / 6.0, 1.0)
    elif score <= -1:
        action = "SELL"
        strength = abs(score) / 6.0
    else:
        action = "HOLD"
        strength = 0.0

    # Target and stop-loss based on ATR
    high = df["High"].tail(14)
    low = df["Low"].tail(14)
    atr = float((high - low).mean())
    target_price = round(current_price + 2 * atr, 2) if "BUY" in action else round(current_price - 2 * atr, 2)
    stop_loss = round(current_price - 1.5 * atr, 2) if "BUY" in action else round(current_price + 1.5 * atr, 2)

    return {
        "action": action,
        "score": score,
        "strength": round(strength, 2),
        "current_price": round(current_price, 2),
        "target_price": target_price,
        "stop_loss": stop_loss,
        "rsi": round(rsi, 2),
        "macd_crossover": "BULLISH" if macd > signal_line else "BEARISH",
        "trend": "UPTREND" if current_price > sma20 > sma50 else ("DOWNTREND" if current_price < sma20 < sma50 else "SIDEWAYS"),
        "volume_confirmed": vol_confirm,
        "reasons": reasons,
    }


@app.post("/tools/generate_buy_sell_signals")
async def generate_buy_sell_signals(req: SignalRequest):
    results = []

    for sym in req.symbols:
        sym = sym.upper()
        cache_key = f"signal:{sym}"
        cached = await redis_client.get(cache_key)

        if cached:
            results.append(json.loads(cached))
            continue

        try:
            ticker = yf.Ticker(sym)
            df = ticker.history(period="6mo")
            if df.empty or len(df) < 60:
                results.append({"symbol": sym, "action": "INSUFFICIENT_DATA", "error": "Not enough history"})
                continue

            signal = compute_signal_score(df)
            signal["symbol"] = sym
            signal["timestamp"] = datetime.utcnow().isoformat()

            await redis_client.setex(cache_key, 300, json.dumps(signal))
            results.append(signal)
            logger.info(f"Signal for {sym}: {signal['action']} (score={signal['score']})")

        except Exception as e:
            logger.error(f"Signal failed for {sym}: {e}")
            results.append({"symbol": sym, "action": "ERROR", "error": str(e)})

    # Sort by absolute score (strongest signals first)
    results.sort(key=lambda x: abs(x.get("score", 0)), reverse=True)

    buys = [r for r in results if "BUY" in r.get("action", "")]
    sells = [r for r in results if "SELL" in r.get("action", "")]

    return {
        "risk_profile": req.risk_profile,
        "total_analyzed": len(results),
        "buy_signals": len(buys),
        "sell_signals": len(sells),
        "signals": results,
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.post("/tools/risk_alerts")
async def risk_alerts(req: RiskAlertRequest):
    """Portfolio risk assessment and alert generation"""
    try:
        ticker = yf.Ticker(req.symbol.upper())
        df = ticker.history(period="6mo")
        if df.empty:
            raise HTTPException(status_code=404, detail=f"No data for {req.symbol}")

        returns = df["Close"].pct_change().dropna()
        vol = float(returns.std()) * np.sqrt(252) * 100
        max_drawdown = float(((df["Close"] / df["Close"].cummax()) - 1).min() * 100)

        # VaR 95% (daily)
        var_95 = float(np.percentile(returns, 5) * 100)

        alerts = []
        if vol > 50:
            alerts.append({"level": "HIGH", "message": f"Annualized volatility {vol:.1f}% is very high"})
        if max_drawdown < -30:
            alerts.append({"level": "HIGH", "message": f"Max drawdown {max_drawdown:.1f}% is severe"})
        if var_95 < -3:
            alerts.append({"level": "MEDIUM", "message": f"Daily VaR(95%) = {var_95:.2f}% — significant downside risk"})

        if not alerts:
            alerts.append({"level": "LOW", "message": "Risk metrics within normal range"})

        return {
            "symbol": req.symbol.upper(),
            "volatility_annualized_pct": round(vol, 2),
            "max_drawdown_pct": round(max_drawdown, 2),
            "var_95_daily_pct": round(var_95, 3),
            "alerts": alerts,
            "overall_risk": "HIGH" if any(a["level"] == "HIGH" for a in alerts) else "MEDIUM" if any(a["level"] == "MEDIUM" for a in alerts) else "LOW",
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    return {"status": "healthy"}
