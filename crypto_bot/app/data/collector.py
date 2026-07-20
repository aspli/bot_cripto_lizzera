import ccxt
import pandas as pd
import logging
from app.config.settings import settings
from app.data.models import Candle, SessionLocal
import datetime

logger = logging.getLogger(__name__)

class DataCollector:
    def __init__(self):
        self.exchange = ccxt.binance({
            'enableRateLimit': True,
        })
        if settings.BINANCE_API_KEY and settings.BINANCE_SECRET_KEY:
            self.exchange.apiKey = settings.BINANCE_API_KEY
            self.exchange.secret = settings.BINANCE_SECRET_KEY

    def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int = 500) -> pd.DataFrame:
        """Fetches OHLCV data from the exchange."""
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            logger.error(f"Error fetching data for {symbol} {timeframe}: {e}")
            return pd.DataFrame()

    def update_database(self):
        """Fetches recent data for all configured symbols and timeframes and updates DB."""
        db = SessionLocal()
        try:
            for symbol in settings.SYMBOLS:
                for timeframe in settings.TIMEFRAMES:
                    logger.info(f"Fetching data for {symbol} {timeframe}")
                    df = self.fetch_ohlcv(symbol, timeframe, limit=100) # Fetch recent 100 candles
                    if df.empty:
                        continue

                    # Store in db
                    for _, row in df.iterrows():
                        # Check if exists
                        exists = db.query(Candle).filter(
                            Candle.symbol == symbol,
                            Candle.timeframe == timeframe,
                            Candle.timestamp == row['timestamp']
                        ).first()

                        if not exists:
                            candle = Candle(
                                symbol=symbol,
                                timeframe=timeframe,
                                timestamp=row['timestamp'],
                                open=row['open'],
                                high=row['high'],
                                low=row['low'],
                                close=row['close'],
                                volume=row['volume']
                            )
                            db.add(candle)
            db.commit()
        except Exception as e:
            logger.error(f"Database update failed: {e}")
            db.rollback()
        finally:
            db.close()
