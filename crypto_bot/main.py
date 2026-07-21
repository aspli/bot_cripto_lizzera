import time
import logging
from app.config.settings import settings
from app.data.models import init_db
from app.data.collector import DataCollector
from app.strategies.trend_following import TrendFollowingStrategy
from app.risk_management.manager import RiskManager
from app.execution.executor import Executor
from app.notifications.telegram import TelegramNotifier

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    logger.info("Initializing Crypto Bot...")
    init_db()

    collector = DataCollector()
    strategy = TrendFollowingStrategy()
    risk_manager = RiskManager()
    notifier = TelegramNotifier()
    executor = Executor(notifier=notifier)

    logger.info("Bot started successfully. Listening for signals...")
    notifier.send_message("🤖 Crypto Bot started.")

    while True:
        try:
            logger.info("Fetching new data...")
            collector.update_database()

            for symbol in settings.SYMBOLS:
                # Assuming 1h timeframe for main trend trading
                df = collector.fetch_ohlcv(symbol, '1h', limit=250)
                if df.empty:
                    continue

                df_signals = strategy.generate_signals(df)
                latest_signal = df_signals.iloc[-2]['signal']
                latest_price = df_signals.iloc[-1]['close']

                if latest_signal == 1:
                    logger.info(f"BUY signal generated for {symbol}")
                    if risk_manager.can_open_trade(symbol):
                        qty = risk_manager.calculate_position_size(settings.PAPER_TRADING_BALANCE, latest_price) / latest_price
                        executor.execute_order(symbol, "buy", qty, latest_price)

                elif latest_signal == -1:
                    logger.info(f"SELL signal generated for {symbol}")
                    # Close long positions if they exist
                    from app.data.models import SessionLocal, Trade
                    db = SessionLocal()
                    try:
                        open_trades = db.query(Trade).filter(Trade.symbol == symbol, Trade.status == 'open', Trade.side == 'buy').all()
                        for trade in open_trades:
                            executor.close_order(trade.id, latest_price)
                    finally:
                        db.close()

            logger.info("Sleeping for 60 seconds...")
            time.sleep(60)

        except KeyboardInterrupt:
            logger.info("Bot stopped by user.")
            notifier.send_message("🛑 Crypto Bot stopped.")
            break
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
