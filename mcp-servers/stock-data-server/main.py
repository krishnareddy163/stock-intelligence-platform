from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import yfinance as yf
import redis.asyncio as aioredis
import json
import logging
import os
from datetime import datetime

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


app = FastAPI(title="Stock Data MCP Server", version="1.0.0", lifespan=lifespan)


class StockPriceRequest(BaseModel):
    symbol: str


class HistoricalRequest(BaseModel):
    symbol: str
    days: int = 365


class IndexRequest(BaseModel):
    index: str


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/tools/get_stock_price")
async def get_stock_price(request: StockPriceRequest):
    try:
        symbol = request.symbol.upper()
        cache_key = f"stock:{symbol}:price"

        cached = await redis_client.get(cache_key)
        if cached:
            logger.info(f"Cache hit for {symbol}")
            return json.loads(cached)

        ticker = yf.Ticker(symbol)
        data = ticker.history(period="2d")

        if data.empty:
            raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")

        latest = data.iloc[-1]
        previous_close = data.iloc[-2]["Close"] if len(data) > 1 else latest["Close"]

        response = {
            "symbol": symbol,
            "price": round(float(latest["Close"]), 2),
            "change_percent": round(float((latest["Close"] - previous_close) / previous_close * 100), 2),
            "volume": int(latest["Volume"]),
            "timestamp": datetime.now().isoformat(),
        }

        await redis_client.setex(cache_key, 60, json.dumps(response))
        logger.info(f"Stock price fetched for {symbol}: {response['price']}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching stock price for {request.symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tools/get_historical_data")
async def get_historical_data(request: HistoricalRequest):
    try:
        symbol = request.symbol.upper()
        ticker = yf.Ticker(symbol)
        data = ticker.history(period=f"{request.days}d")

        if data.empty:
            raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")

        historical_data = [
            {
                "date": date.strftime("%Y-%m-%d"),
                "open": round(float(row["Open"]), 2),
                "high": round(float(row["High"]), 2),
                "low": round(float(row["Low"]), 2),
                "close": round(float(row["Close"]), 2),
                "volume": int(row["Volume"]),
            }
            for date, row in data.iterrows()
        ]

        logger.info(f"Historical data fetched for {symbol}: {len(historical_data)} records")
        return {"symbol": symbol, "data": historical_data}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching historical data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tools/get_market_index_data")
async def get_market_index_data(request: IndexRequest):
    index_map = {
        "NIFTY50": "^NSEI",
        "SENSEX": "^BSESN",
        "NASDAQ": "^IXIC",
        "SP500": "^GSPC",
        "NIKKEI": "^N225",
        "FTSE": "^FTSE",
    }
    try:
        ticker_symbol = index_map.get(request.index.upper(), request.index.upper())
        cache_key = f"index:{ticker_symbol}"

        cached = await redis_client.get(cache_key)
        if cached:
            return json.loads(cached)

        ticker = yf.Ticker(ticker_symbol)
        data = ticker.history(period="2d")

        if data.empty:
            raise HTTPException(status_code=404, detail=f"Index {request.index} not found")

        latest = data.iloc[-1]
        previous_close = data.iloc[-2]["Close"] if len(data) > 1 else latest["Close"]

        response = {
            "index": request.index,
            "symbol": ticker_symbol,
            "value": round(float(latest["Close"]), 2),
            "change_percent": round(float((latest["Close"] - previous_close) / previous_close * 100), 2),
            "timestamp": datetime.now().isoformat(),
        }

        await redis_client.setex(cache_key, 60, json.dumps(response))
        logger.info(f"Index data fetched for {request.index}: {response['value']}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching index data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001)
