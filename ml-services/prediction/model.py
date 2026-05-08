"""
LSTM + XGBoost Ensemble for stock price forecasting
"""
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_percentage_error
import joblib
import os
import logging

logger = logging.getLogger(__name__)

try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch not available — LSTM disabled, using XGBoost only")

SEQUENCE_LENGTH = 60  # 60 trading days lookback


class LSTMModel(nn.Module if TORCH_AVAILABLE else object):
    def __init__(self, input_size=10, hidden_size=128, num_layers=2, dropout=0.2):
        if TORCH_AVAILABLE:
            super().__init__()
            self.lstm = nn.LSTM(
                input_size=input_size,
                hidden_size=hidden_size,
                num_layers=num_layers,
                dropout=dropout,
                batch_first=True,
            )
            self.attention = nn.MultiheadAttention(hidden_size, num_heads=4, batch_first=True)
            self.fc = nn.Sequential(
                nn.Linear(hidden_size, 64),
                nn.ReLU(),
                nn.Dropout(0.1),
                nn.Linear(64, 1),
            )

    def forward(self, x):
        lstm_out, _ = self.lstm(x)
        attn_out, _ = self.attention(lstm_out, lstm_out, lstm_out)
        out = self.fc(attn_out[:, -1, :])
        return out.squeeze(-1)


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create feature matrix from OHLCV data"""
    df = df.copy()
    df["returns"] = df["Close"].pct_change()
    df["log_returns"] = np.log(df["Close"] / df["Close"].shift(1))
    df["sma_5"] = df["Close"].rolling(5).mean()
    df["sma_20"] = df["Close"].rolling(20).mean()
    df["sma_50"] = df["Close"].rolling(50).mean()
    df["ema_12"] = df["Close"].ewm(span=12).mean()
    df["ema_26"] = df["Close"].ewm(span=26).mean()
    df["macd"] = df["ema_12"] - df["ema_26"]
    df["volatility"] = df["returns"].rolling(10).std()
    df["volume_change"] = df["Volume"].pct_change()
    df["price_range"] = (df["High"] - df["Low"]) / df["Close"]

    delta = df["Close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    df["rsi"] = 100 - (100 / (1 + gain / (loss + 1e-9)))

    df["bb_upper"] = df["Close"].rolling(20).mean() + 2 * df["Close"].rolling(20).std()
    df["bb_lower"] = df["Close"].rolling(20).mean() - 2 * df["Close"].rolling(20).std()
    df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / df["Close"]

    return df.dropna()


FEATURE_COLS = [
    "returns", "log_returns", "sma_5", "sma_20", "sma_50",
    "ema_12", "ema_26", "macd", "volatility", "rsi",
    "bb_width", "price_range", "volume_change",
]


class EnsemblePredictor:
    """LSTM + XGBoost ensemble with weighted average"""

    def __init__(self, symbol: str, model_dir: str = "./models"):
        self.symbol = symbol
        self.model_dir = model_dir
        self.scaler = MinMaxScaler()
        self.target_scaler = MinMaxScaler()
        self.lstm_model = None
        self.xgb_model = None
        os.makedirs(model_dir, exist_ok=True)

    def prepare_sequences(self, X: np.ndarray, y: np.ndarray):
        """Build (seq_len, features) sequences for LSTM"""
        if not TORCH_AVAILABLE:
            return None, None
        Xs, ys = [], []
        for i in range(SEQUENCE_LENGTH, len(X)):
            Xs.append(X[i - SEQUENCE_LENGTH:i])
            ys.append(y[i])
        return np.array(Xs), np.array(ys)

    def train(self, df: pd.DataFrame, epochs: int = 50) -> dict:
        df = build_features(df)
        if len(df) < SEQUENCE_LENGTH + 30:
            raise ValueError(f"Need at least {SEQUENCE_LENGTH + 30} rows, got {len(df)}")

        X = df[FEATURE_COLS].values
        y = df["Close"].values.reshape(-1, 1)

        split = int(len(X) * 0.85)
        X_train, X_test = X[:split], X[split:]
        y_train, y_test = y[:split], y[split:]

        X_train_s = self.scaler.fit_transform(X_train)
        X_test_s = self.scaler.transform(X_test)
        y_train_s = self.target_scaler.fit_transform(y_train).ravel()

        metrics = {}

        # ── XGBoost ──────────────────────────────────────────────
        try:
            from xgboost import XGBRegressor
            self.xgb_model = XGBRegressor(
                n_estimators=500, learning_rate=0.03, max_depth=5,
                subsample=0.8, colsample_bytree=0.8, random_state=42,
                early_stopping_rounds=20, eval_metric="mape",
            )
            self.xgb_model.fit(X_train_s, y_train_s,
                               eval_set=[(X_test_s, self.target_scaler.transform(y_test).ravel())],
                               verbose=False)
            y_pred_xgb = self.target_scaler.inverse_transform(
                self.xgb_model.predict(X_test_s).reshape(-1, 1)
            )
            metrics["xgb_mape"] = round(mean_absolute_percentage_error(y_test, y_pred_xgb) * 100, 2)
            logger.info(f"XGBoost MAPE: {metrics['xgb_mape']:.2f}%")
        except ImportError:
            logger.warning("XGBoost not installed")

        # ── LSTM ─────────────────────────────────────────────────
        if TORCH_AVAILABLE:
            Xs_train, ys_train = self.prepare_sequences(X_train_s, y_train_s)
            Xs_test, ys_test = self.prepare_sequences(X_test_s,
                self.target_scaler.transform(y_test).ravel())

            self.lstm_model = LSTMModel(input_size=len(FEATURE_COLS), hidden_size=128, num_layers=2)
            optimizer = torch.optim.AdamW(self.lstm_model.parameters(), lr=1e-3, weight_decay=1e-4)
            scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
            criterion = nn.HuberLoss()

            X_t = torch.FloatTensor(Xs_train)
            y_t = torch.FloatTensor(ys_train)

            self.lstm_model.train()
            for epoch in range(epochs):
                optimizer.zero_grad()
                pred = self.lstm_model(X_t)
                loss = criterion(pred, y_t)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.lstm_model.parameters(), 1.0)
                optimizer.step()
                scheduler.step()
                if (epoch + 1) % 10 == 0:
                    logger.info(f"Epoch {epoch+1}/{epochs} — Loss: {loss.item():.6f}")

            self.lstm_model.eval()
            with torch.no_grad():
                X_te = torch.FloatTensor(Xs_test)
                y_pred_lstm = self.target_scaler.inverse_transform(
                    self.lstm_model(X_te).numpy().reshape(-1, 1)
                )
                metrics["lstm_mape"] = round(
                    mean_absolute_percentage_error(y_test[SEQUENCE_LENGTH:], y_pred_lstm) * 100, 2
                )
                logger.info(f"LSTM MAPE: {metrics['lstm_mape']:.2f}%")

        self._save()
        return metrics

    def predict(self, df: pd.DataFrame, forecast_days: int = 30) -> list[dict]:
        df = build_features(df)
        X = self.scaler.transform(df[FEATURE_COLS].values)
        last_price = float(df["Close"].iloc[-1])
        predictions = []

        # XGBoost rolling forecast
        xgb_preds = []
        if self.xgb_model is not None:
            last_features = X[-1].copy()
            for _ in range(forecast_days):
                pred_s = self.xgb_model.predict(last_features.reshape(1, -1))[0]
                pred_price = float(self.target_scaler.inverse_transform([[pred_s]])[0][0])
                xgb_preds.append(pred_price)
                # Shift features forward (simplified)
                last_features = np.roll(last_features, -1)
                last_features[-1] = pred_s

        # LSTM rolling forecast
        lstm_preds = []
        if TORCH_AVAILABLE and self.lstm_model is not None and len(X) >= SEQUENCE_LENGTH:
            seq = torch.FloatTensor(X[-SEQUENCE_LENGTH:]).unsqueeze(0)
            self.lstm_model.eval()
            with torch.no_grad():
                for _ in range(forecast_days):
                    pred_s = self.lstm_model(seq).item()
                    pred_price = float(self.target_scaler.inverse_transform([[pred_s]])[0][0])
                    lstm_preds.append(pred_price)
                    new_step = torch.FloatTensor(seq[0, -1].numpy())
                    new_step[-1] = pred_s
                    seq = torch.cat([seq[:, 1:, :], new_step.unsqueeze(0).unsqueeze(0)], dim=1)

        # Ensemble (60% XGB + 40% LSTM if both available, else fallback)
        vol = float(df["volatility"].iloc[-1]) * last_price
        for i in range(forecast_days):
            if xgb_preds and lstm_preds:
                price = 0.6 * xgb_preds[i] + 0.4 * lstm_preds[i]
            elif xgb_preds:
                price = xgb_preds[i]
            elif lstm_preds:
                price = lstm_preds[i]
            else:
                break
            predictions.append({
                "day": i + 1,
                "predicted_price": round(max(price, last_price * 0.3), 2),
                "ci_lower": round(max(price - 1.96 * vol, 0), 2),
                "ci_upper": round(price + 1.96 * vol, 2),
            })

        return predictions

    def _save(self):
        if self.xgb_model:
            joblib.dump(self.xgb_model, f"{self.model_dir}/{self.symbol}_xgb.pkl")
        joblib.dump(self.scaler, f"{self.model_dir}/{self.symbol}_scaler.pkl")
        joblib.dump(self.target_scaler, f"{self.model_dir}/{self.symbol}_target_scaler.pkl")
        if TORCH_AVAILABLE and self.lstm_model:
            torch.save(self.lstm_model.state_dict(), f"{self.model_dir}/{self.symbol}_lstm.pt")
        logger.info(f"Model saved for {self.symbol}")

    def load(self):
        self.scaler = joblib.load(f"{self.model_dir}/{self.symbol}_scaler.pkl")
        self.target_scaler = joblib.load(f"{self.model_dir}/{self.symbol}_target_scaler.pkl")
        xgb_path = f"{self.model_dir}/{self.symbol}_xgb.pkl"
        if os.path.exists(xgb_path):
            self.xgb_model = joblib.load(xgb_path)
        lstm_path = f"{self.model_dir}/{self.symbol}_lstm.pt"
        if TORCH_AVAILABLE and os.path.exists(lstm_path):
            self.lstm_model = LSTMModel(input_size=len(FEATURE_COLS))
            self.lstm_model.load_state_dict(torch.load(lstm_path, map_location="cpu"))
            self.lstm_model.eval()
        return self
