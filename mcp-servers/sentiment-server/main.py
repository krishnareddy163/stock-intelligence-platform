"""
News & Social Sentiment MCP Server
Fetches news via NewsAPI, scores with HuggingFace FinBERT, caches in Redis
"""
import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
import httpx
import redis.asyncio as aioredis
from fastapi import FastAPI
from pydantic import BaseModel
from transformers import pipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

redis_client: aioredis.Redis = None
sentiment_model = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_client, sentiment_model
    redis_client = aioredis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    try:
        # FinBERT — fine-tuned for financial sentiment
        sentiment_model = pipeline(
            "sentiment-analysis",
            model="ProsusAI/finbert",
            max_length=512,
            truncation=True,
        )
        logger.info("FinBERT model loaded")
    except Exception as e:
        logger.warning(f"FinBERT unavailable, falling back to rule-based: {e}")
        sentiment_model = None
    yield
    await redis_client.aclose()


app = FastAPI(title="Sentiment MCP Server", version="1.0.0", lifespan=lifespan)


class SentimentRequest(BaseModel):
    symbol: str
    days: int = 7


def rule_based_sentiment(text: str) -> float:
    """Fallback keyword-based sentiment when model unavailable"""
    positive = ["surge", "rally", "beat", "record", "growth", "profit", "buy", "upgrade", "strong", "gain"]
    negative = ["crash", "drop", "miss", "loss", "debt", "sell", "downgrade", "weak", "decline", "risk"]
    text_lower = text.lower()
    pos = sum(1 for w in positive if w in text_lower)
    neg = sum(1 for w in negative if w in text_lower)
    total = pos + neg
    if total == 0:
        return 0.0
    return (pos - neg) / total


async def score_texts(texts: list[str]) -> list[float]:
    """Return sentiment scores in [-1, 1] for each text"""
    if not texts:
        return []
    if sentiment_model:
        results = sentiment_model(texts[:20])  # limit batch size
        score_map = {"positive": 1.0, "negative": -1.0, "neutral": 0.0}
        return [score_map.get(r["label"].lower(), 0.0) * r["score"] for r in results]
    return [rule_based_sentiment(t) for t in texts]


async def fetch_news(symbol: str, days: int) -> list[dict]:
    """Fetch news from NewsAPI"""
    if not NEWSAPI_KEY:
        return []

    from_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": symbol,
        "from": from_date,
        "sortBy": "relevancy",
        "pageSize": 20,
        "language": "en",
        "apiKey": NEWSAPI_KEY,
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            articles = resp.json().get("articles", [])
            return [{"title": a["title"], "description": a.get("description", ""), "source": a["source"]["name"]} for a in articles]
        except Exception as e:
            logger.error(f"NewsAPI error: {e}")
            return []


@app.post("/tools/get_news_sentiment")
async def get_news_sentiment(req: SentimentRequest):
    cache_key = f"sentiment:{req.symbol}:{req.days}d"
    cached = await redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    articles = await fetch_news(req.symbol, req.days)

    if not articles:
        result = {
            "symbol": req.symbol,
            "sentiment_score": 0.0,
            "sentiment_label": "NEUTRAL",
            "article_count": 0,
            "headlines": [],
            "timestamp": datetime.utcnow().isoformat(),
        }
        await redis_client.setex(cache_key, 300, json.dumps(result))
        return result

    texts = [f"{a['title']} {a.get('description', '')}" for a in articles]
    scores = await score_texts(texts)
    avg_score = sum(scores) / len(scores) if scores else 0.0

    label = "BULLISH" if avg_score > 0.15 else ("BEARISH" if avg_score < -0.15 else "NEUTRAL")

    result = {
        "symbol": req.symbol,
        "sentiment_score": round(avg_score, 4),
        "sentiment_label": label,
        "article_count": len(articles),
        "headlines": [a["title"] for a in articles[:5]],
        "sources": list({a["source"] for a in articles[:5]}),
        "timestamp": datetime.utcnow().isoformat(),
    }

    await redis_client.setex(cache_key, 300, json.dumps(result))
    logger.info(f"Sentiment for {req.symbol}: {label} ({avg_score:.3f})")
    return result


@app.post("/tools/get_social_sentiment")
async def get_social_sentiment(req: SentimentRequest):
    """Placeholder for Reddit/Twitter sentiment — returns simulated data"""
    cache_key = f"social_sentiment:{req.symbol}"
    cached = await redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    import random
    rng = random.Random(req.symbol + str(datetime.utcnow().date()))
    reddit_score = round(rng.uniform(-0.5, 0.8), 3)
    twitter_score = round(rng.uniform(-0.4, 0.7), 3)
    combined = round((reddit_score + twitter_score) / 2, 3)

    result = {
        "symbol": req.symbol,
        "reddit_score": reddit_score,
        "twitter_score": twitter_score,
        "combined_score": combined,
        "label": "BULLISH" if combined > 0.1 else ("BEARISH" if combined < -0.1 else "NEUTRAL"),
        "note": "Social sentiment requires live Reddit/Twitter API keys",
        "timestamp": datetime.utcnow().isoformat(),
    }

    await redis_client.setex(cache_key, 600, json.dumps(result))
    return result


@app.get("/health")
async def health():
    return {"status": "healthy", "model": "finbert" if sentiment_model else "rule-based"}
