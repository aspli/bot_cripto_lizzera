import logging
import pandas as pd
from backtesting import Backtest, Strategy
import pandas_ta as ta
from app.data.collector import DataCollector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# To use backtesting.py, we need to adapt the strategy logic
class TrendFollowingBT(Strategy):
    n_ema1 = 20
    n_ema2 = 50
    n_ema3 = 200
    n_rsi = 14

    def init(self):
        close = pd.Series(self.data.Close)
        self.ema20 = self.I(ta.ema, close, length=self.n_ema1)
        self.ema50 = self.I(ta.ema, close, length=self.n_ema2)
        self.ema200 = self.I(ta.ema, close, length=self.n_ema3)
        self.rsi = self.I(ta.rsi, close, length=self.n_rsi)

    def next(self):
        if not self.position:
            if self.ema20[-1] > self.ema50[-1] and self.rsi[-1] > 55 and self.data.Close[-1] > self.ema200[-1]:
                self.buy(sl=self.data.Close[-1] * 0.98, tp=self.data.Close[-1] * 1.04)
        else:
            if self.ema20[-1] < self.ema50[-1] or self.rsi[-1] < 45:
                self.position.close()

def run_backtest():
    collector = DataCollector()
    logger.info("Fetching historical data for backtest...")
    df = collector.fetch_ohlcv('BTC/USDT', '1h', limit=1000)

    if df.empty:
        logger.error("No data fetched.")
        return

    # Backtesting.py requires columns to be capitalized
    df.rename(columns={
        'timestamp': 'Date',
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume'
    }, inplace=True)
    df.set_index('Date', inplace=True)

    bt = Backtest(df, TrendFollowingBT, cash=10000, commission=.001, exclusive_orders=True)
    stats = bt.run()

    print("\n=== Backtest Results ===")
    print(stats)

    # bt.plot() # Uncomment to see visual chart (requires bokeh)

if __name__ == "__main__":
    run_backtest()
