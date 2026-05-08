import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    claude_model: str = "claude-sonnet-4-6"

    mcp_stock_data_url: str = os.getenv("MCP_STOCK_DATA_URL", "http://stock-data-server:5001")
    mcp_sentiment_url: str = os.getenv("MCP_SENTIMENT_URL", "http://sentiment-server:5002")
    mcp_prediction_url: str = os.getenv("MCP_PREDICTION_URL", "http://prediction-server:5003")
    mcp_portfolio_url: str = os.getenv("MCP_PORTFOLIO_URL", "http://portfolio-server:5004")
    mcp_technical_url: str = os.getenv("MCP_TECHNICAL_URL", "http://technical-analysis-server:5005")
    mcp_alert_url: str = os.getenv("MCP_ALERT_URL", "http://alert-server:5006")

    class Config:
        env_file = ".env"


settings = Settings()
