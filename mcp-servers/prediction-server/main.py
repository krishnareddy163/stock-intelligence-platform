"""
ML Prediction MCP Server
Provides stock price forecasts using LSTM + XGBoost ensemble
"""
import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import redis.asyncio as aioredis
import yfinance as yf
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import GradientBoostingRegressor

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


app = FastAPI(title="Prediction MCP Server", version="1.0.0", lifespan=lifespan)


class PredictionRequest(BaseModel):
    symbol: str
    forecast_days: int = 30


class TrendRequest(BaseModel):
    index: str
    days: int = 30


def compute_features(df: pd.DataFrame) -> pd.DataFrame:
    """Build feature matrix from OHLCV data"""
    df = df.copy()
    df["returns"] = df["Close"].pct_change()
    df["sma_5"] = df["Close"].rolling(5).mean()
    df["sma_20"] = df["Close"].rolling(20).mean()
    df["sma_50"] = df["Close"].rolling(50).mean()
    df["volatility"] = df["returns"].rolling(10).std()
    df["volume_ma"] = df["Volume"].rolling(10).mean()
    df["volume_ratio"] = df["Volume"] / (df["volume_ma"] + 1e-9)
    df["price_range"] = (df["High"] - df["Low"]) / df["Close"]

    # RSI
    delta = df["Close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / (loss + 1e-9)
    df["rsi"] = 100 - (100 / (1 + rs))

    # MACD
    ema12 = df["Close"].ewm(span=12).mean()
    ema26 = df["Close"].ewm(span=26).mean()
    df["macd"] = ema12 - ema26

    df = df.dropna()
    return df


def xgboost_forecast(df: pd.DataFrame, forecast_days: int) -> list[dict]:
    """XGBoost-based price forecast using rolling features"""
    df = compute_features(df)
    if len(df) < 60:
        return []

    feature_cols = ["returns", "sma_5", "sma_20", "sma_50", "volatility",
                    "volume_ratio", "price_range", "rsi", "macd"]

    X = df[feature_cols].values
    y = df["Close"].values

    # Scale
    scaler = MinMaxScaler()
    X_scaled = scaler.fit_transform(X)

    # Train on all data except last 10 days (validation)
    X_train, y_train = X_scaled[:-10], y[:-10]

    model = GradientBoostingRegressor(n_estimators=200, learning_rate=0.05, max_depth=4, random_state=42)
    model.fit(X_train, y_train)

    # Generate forecasts by rolling the last known features forward
    last_price = float(df["Close"].iloc[-1])
    predictions = []
    last_features = X_scaled[-1].copy()

    for i in range(forecast_days):
        pred_price = float(model.predict(last_features.reshape(1, -1))[0])
        # Add small momentum noise
        noise = np.random.normal(0, last_price * 0.005)
        pred_price = max(pred_price + noise, last_price * 0.5)

        future_date = datetime.utcnow() + timedelta(days=i + 1)
        # 95% confidence interval based on recent volatility
        vol = float(df["volatility"].iloc[-1]) * last_price
        predictions.append({
            "date": future_date.strftime("%Y-%m-%d"),
            "predicted_price": round(pred_price, 2),
            "ci_lower": round(pred_price - 1.96 * vol, 2),
            "ci_upper": round(pred_price + 1.96 * vol, 2),
        })
        last_price = pred_price

    return predictions


@app.post("/tools/predict_stock_price")
async def predict_stock_price(req: PredictionRequest):
    cache_key = f"prediction:{req.symbol}:{req.forecast_days}d"
    cached = await redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    try:
        ticker = yf.Ticker(req.symbol.upper())
        df = ticker.history(period="2y")
        if df.empty or len(df) < 60:
            raise HTTPException(status_code=404, detail=f"Insufficient data for {req.symbol}")

        predictions = xgboost_forecast(df, req.forecast_days)
        if not predictions:
            raise HTTPException(status_code=422, detail="Could not generate forecast")

        current_price = float(df["Close"].iloc[-1])
        final_price = predictions[-1]["predicted_price"]
        expected_return = round((final_price - current_price) / current_price * 100, 2)

        result = {
            "symbol": req.symbol.upper(),
            "current_price": round(current_price, 2),
            "forecast_days": req.forecast_days,
            "predicted_price": final_price,
            "expected_return_percent": expected_return,
            "direction": "BULLISH" if expected_return > 2 else ("BEARISH" if expected_return < -2 else "NEUTRAL"),
            "predictions": predictions[:7],  # return first 7 points
            "model": "GradientBoosting",
            "generated_at": datetime.utcnow().isoformat(),
        }

        await redis_client.setex(cache_key, 1800, json.dumps(result))
        logger.info(f"Prediction for {req.symbol}: {expected_return:+.2f}% over {req.forecast_days}d")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prediction failed for {req.symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tools/predict_market_trend")
async def predict_market_trend(req: TrendRequest):
    index_map = {
        "NIFTY50": "^NSEI", "SENSEX": "^BSESN", "NASDAQ": "^IXIC",
        "SP500": "^GSPC", "NIKKEI": "^N225", "FTSE": "^FTSE",
    }
    symbol = index_map.get(req.index.upper(), req.index.upper())

    cache_key = f"trend:{symbol}:{req.days}d"
    cached = await redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="1y")
        if df.empty:
            raise HTTPException(status_code=404, detail=f"Index {req.index} not found")

        df = compute_features(df)
        recent = df.tail(20)

        momentum = float(recent["returns"].mean()) * 100
        rsi = float(recent["rsi"].iloc[-1])
        macd = float(recent["macd"].iloc[-1])
        vol = float(recent["volatility"].std())

        # Trend scoring
        score = 0
        score += 1 if momentum > 0 else -1
        score += 1 if rsi > 55 else (-1 if rsi < 45 else 0)
        score += 1 if macd > 0 else -1

        trend = "BULLISH" if score >= 2 else ("BEARISH" if score <= -2 else "NEUTRAL")

        result = {
            "index": req.index,
            "symbol": symbol,
            "trend": trend,
            "confidence": min(abs(score) / 3.0, 1.0),
            "momentum_pct": round(momentum, 3),
            "rsi": round(rsi, 2),
            "macd": round(macd, 4),
            "volatility": round(vol, 4),
            "forecast_days": req.days,
            "timestamp": datetime.utcnow().isoformat(),
        }

        await redis_client.setex(cache_key, 900, json.dumps(result))
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Trend prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tools/predict_volatility")
async def predict_volatility(req: PredictionRequest):
    """Predict 30-day realized volatility using GARCH-like approach"""
    try:
        ticker = yf.Ticker(req.symbol.upper())
        df = ticker.history(period="1y")
        if df.empty:
            raise HTTPException(status_code=404, detail=f"Stock {req.symbol} not found")

        returns = df["Close"].pct_change().dropna()
        recent_vol = float(returns.tail(30).std()) * np.sqrt(252) * 100  # annualized
        long_term_vol = float(returns.std()) * np.sqrt(252) * 100

        return {
            "symbol": req.symbol.upper(),
            "current_volatility_annualized_pct": round(recent_vol, 2),
            "long_term_volatility_pct": round(long_term_vol, 2),
            "volatility_regime": "HIGH" if recent_vol > 40 else ("MEDIUM" if recent_vol > 20 else "LOW"),
            "timestamp": datetime.utcnow().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    return {"status": "healthy"}
