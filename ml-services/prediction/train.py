"""
CLI training script: python train.py --symbol AAPL --epochs 100
"""
import argparse
import logging
import yfinance as yf
from model import EnsemblePredictor

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

UNIVERSE = {
    "US": ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "JPM", "JNJ", "V"],
    "IN": ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS"],
    "JP": ["7203.T", "6758.T", "9984.T"],
    "UK": ["HSBA.L", "BP.L", "SHEL.L"],
}


def train_symbol(symbol: str, epochs: int, model_dir: str):
    logger.info(f"Training model for {symbol}")
    ticker = yf.Ticker(symbol)
    df = ticker.history(period="5y")
    if df.empty or len(df) < 200:
        logger.warning(f"Insufficient data for {symbol}, skipping")
        return

    predictor = EnsemblePredictor(symbol, model_dir)
    metrics = predictor.train(df, epochs=epochs)
    logger.info(f"Training complete for {symbol}: {metrics}")


def main():
    parser = argparse.ArgumentParser(description="Train stock prediction models")
    parser.add_argument("--symbol", help="Single stock symbol (e.g. AAPL)")
    parser.add_argument("--market", choices=list(UNIVERSE.keys()), help="Train all symbols in a market")
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--model-dir", default="./models")
    args = parser.parse_args()

    if args.symbol:
        train_symbol(args.symbol.upper(), args.epochs, args.model_dir)
    elif args.market:
        for sym in UNIVERSE[args.market]:
            try:
                train_symbol(sym, args.epochs, args.model_dir)
            except Exception as e:
                logger.error(f"Failed {sym}: {e}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
