"""
Technical Analysis MCP Server
Computes RSI, MACD, Moving Averages, Bollinger Bands from yfinance data
"""
import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime

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


app = FastAPI(title="Technical Analysis MCP Server", version="1.0.0", lifespan=lifespan)


class TARequest(BaseModel):
    symbol: str
    period: int = 14


def compute_rsi(prices: pd.Series, period: int = 14) -> float:
    delta = prices.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / (loss + 1e-9)
    rsi = 100 - (100 / (1 + rs))
    return float(rsi.iloc[-1])


def compute_macd(prices: pd.Series):
    ema12 = prices.ewm(span=12, adjust=False).mean()
    ema26 = prices.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    hist = macd - signal
    return float(macd.iloc[-1]), float(signal.iloc[-1]), float(hist.iloc[-1])


def compute_bollinger(prices: pd.Series, window: int = 20):
    sma = prices.rolling(window).mean()
    std = prices.rolling(window).std()
    upper = sma + 2 * std
    lower = sma - 2 * std
    return float(upper.iloc[-1]), float(sma.iloc[-1]), float(lower.iloc[-1])


def interpret_signals(rsi: float, macd: float, macd_signal: float,
                       close: float, sma_20: float, sma_50: float) -> dict:
    signals = []

    if rsi < 30:
        signals.append({"indicator": "RSI", "signal": "BUY", "reason": f"RSI={rsi:.1f} oversold"})
    elif rsi > 70:
        signals.append({"indicator": "RSI", "signal": "SELL", "reason": f"RSI={rsi:.1f} overbought"})
    else:
        signals.append({"indicator": "RSI", "signal": "NEUTRAL", "reason": f"RSI={rsi:.1f} normal range"})

    if macd > macd_signal:
        signals.append({"indicator": "MACD", "signal": "BUY", "reason": "MACD crossed above signal"})
    else:
        signals.append({"indicator": "MACD", "signal": "SELL", "reason": "MACD crossed below signal"})

    if close > sma_20 > sma_50:
        signals.append({"indicator": "MA", "signal": "BUY", "reason": "Price > SMA20 > SMA50 (uptrend)"})
    elif close < sma_20 < sma_50:
        signals.append({"indicator": "MA", "signal": "SELL", "reason": "Price < SMA20 < SMA50 (downtrend)"})
    else:
        signals.append({"indicator": "MA", "signal": "NEUTRAL", "reason": "Mixed MA signals"})

    buys = sum(1 for s in signals if s["signal"] == "BUY")
    sells = sum(1 for s in signals if s["signal"] == "SELL")
    overall = "BUY" if buys > sells else ("SELL" if sells > buys else "HOLD")

    return {"overall": overall, "breakdown": signals}


@app.post("/tools/get_technical_indicators")
async def get_technical_indicators(req: TARequest):
    cache_key = f"ta:{req.symbol}:full"
    cached = await redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    try:
        ticker = yf.Ticker(req.symbol.upper())
        df = ticker.history(period="1y")
        if df.empty or len(df) < 60:
            raise HTTPException(status_code=404, detail=f"Insufficient data for {req.symbol}")

        close = df["Close"]
        rsi = compute_rsi(close, req.period)
        macd, macd_signal, macd_hist = compute_macd(close)
        bb_upper, bb_mid, bb_lower = compute_bollinger(close)

        sma_20 = float(close.rolling(20).mean().iloc[-1])
        sma_50 = float(close.rolling(50).mean().iloc[-1])
        sma_200 = float(close.rolling(200).mean().iloc[-1]) if len(close) >= 200 else None
        ema_12 = float(close.ewm(span=12).mean().iloc[-1])
        ema_26 = float(close.ewm(span=26).mean().iloc[-1])

        current_price = float(close.iloc[-1])
        signals = interpret_signals(rsi, macd, macd_signal, current_price, sma_20, sma_50)

        result = {
            "symbol": req.symbol.upper(),
            "current_price": round(current_price, 2),
            "rsi": round(rsi, 2),
            "macd": round(macd, 4),
            "macd_signal": round(macd_signal, 4),
            "macd_histogram": round(macd_hist, 4),
            "sma_20": round(sma_20, 2),
            "sma_50": round(sma_50, 2),
            "sma_200": round(sma_200, 2) if sma_200 else None,
            "ema_12": round(ema_12, 2),
            "ema_26": round(ema_26, 2),
            "bollinger_upper": round(bb_upper, 2),
            "bollinger_mid": round(bb_mid, 2),
            "bollinger_lower": round(bb_lower, 2),
            "signals": signals,
            "timestamp": datetime.utcnow().isoformat(),
        }

        await redis_client.setex(cache_key, 300, json.dumps(result))
        logger.info(f"TA computed for {req.symbol}: {signals['overall']}")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"TA failed for {req.symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tools/get_rsi")
async def get_rsi(req: TARequest):
    ticker = yf.Ticker(req.symbol.upper())
    df = ticker.history(period="6mo")
    if df.empty:
        raise HTTPException(status_code=404, detail=f"No data for {req.symbol}")
    rsi = compute_rsi(df["Close"], req.period)
    return {"symbol": req.symbol.upper(), "rsi": round(rsi, 2), "period": req.period}


@app.post("/tools/get_macd")
async def get_macd(req: TARequest):
    ticker = yf.Ticker(req.symbol.upper())
    df = ticker.history(period="6mo")
    if df.empty:
        raise HTTPException(status_code=404, detail=f"No data for {req.symbol}")
    macd, signal, hist = compute_macd(df["Close"])
    return {
        "symbol": req.symbol.upper(),
        "macd": round(macd, 4),
        "signal": round(signal, 4),
        "histogram": round(hist, 4),
        "crossover": "BULLISH" if macd > signal else "BEARISH",
    }


@app.post("/tools/get_moving_average")
async def get_moving_average(req: TARequest):
    ticker = yf.Ticker(req.symbol.upper())
    df = ticker.history(period="1y")
    if df.empty:
        raise HTTPException(status_code=404, detail=f"No data for {req.symbol}")
    close = df["Close"]
    return {
        "symbol": req.symbol.upper(),
        "sma_20": round(float(close.rolling(20).mean().iloc[-1]), 2),
        "sma_50": round(float(close.rolling(50).mean().iloc[-1]), 2),
        "ema_12": round(float(close.ewm(span=12).mean().iloc[-1]), 2),
        "ema_26": round(float(close.ewm(span=26).mean().iloc[-1]), 2),
        "current_price": round(float(close.iloc[-1]), 2),
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
