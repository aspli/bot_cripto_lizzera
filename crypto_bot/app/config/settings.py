from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # API Configuration
    BINANCE_API_KEY: str = ""
    BINANCE_SECRET_KEY: str = ""

    # Trading Configuration
    TRADING_MODE: str = "paper" # paper or live
    PAPER_TRADING_BALANCE: float = 10000.0

    # Risk Management
    MAX_RISK_PER_TRADE: float = 0.01 # 1%
    MAX_OPEN_TRADES: int = 3
    DEFAULT_STOP_LOSS_PCT: float = 0.02 # 2%
    DEFAULT_TAKE_PROFIT_PCT: float = 0.04 # 4%

    # Database Configuration
    DATABASE_URL: str = "sqlite:///./cryptobot.db" # Default fallback

    # Telegram Configuration
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None

    # Strategy Configuration
    SYMBOLS: list[str] = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
    TIMEFRAMES: list[str] = ["1m", "5m", "15m", "1h"]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
