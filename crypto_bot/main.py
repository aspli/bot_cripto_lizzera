import time
import logging
from app.config.settings import settings
from app.data.models import init_db, SessionLocal, Trade # Importado SessionLocal e Trade
from app.data.collector import DataCollector
from app.strategies.trend_following import TrendFollowingStrategy
from app.risk_management.manager import RiskManager
from app.execution.executor import Executor
from app.notifications.telegram import TelegramNotifier

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_open_trades_sl_tp(executor, current_price, symbol):
    """Verifica se alguma posição aberta atingiu o Stop Loss ou Take Profit."""
    db = SessionLocal()
    try:
        open_trades = db.query(Trade).filter(Trade.symbol == symbol, Trade.status == 'open').all()
        for trade in open_trades:
            if trade.side == 'buy':
                if trade.stop_loss and current_price <= trade.stop_loss:
                    logger.info(f"🛑 STOP LOSS atingido para {symbol}!")
                    executor.close_order(trade.id, current_price)
                elif trade.take_profit and current_price >= trade.take_profit:
                    logger.info(f"✅ TAKE PROFIT atingido para {symbol}!")
                    executor.close_order(trade.id, current_price)
            
            elif trade.side == 'sell': # Caso implemente short no futuro
                if trade.stop_loss and current_price >= trade.stop_loss:
                    executor.close_order(trade.id, current_price)
                elif trade.take_profit and current_price <= trade.take_profit:
                    executor.close_order(trade.id, current_price)
    finally:
        db.close()

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
                df = collector.fetch_ohlcv(symbol, '1h', limit=250)
                if df.empty:
                    continue
                
                df_signals = strategy.generate_signals(df)
                current_signal = df_signals.iloc[-2]['signal']
                previous_signal = df_signals.iloc[-3]['signal']
                
                latest_signal = df_signals.iloc[-2]['signal'] 
                current_price = df_signals.iloc[-1]['close'] 
                
                # 1. VERIFICAR SL e TP PRIMEIRO
                check_open_trades_sl_tp(executor, current_price, symbol)
                
                if previous_signal != 1 and current_signal == 1:
                    if risk_manager.can_open_trade(symbol):
                        logger.info(f"🟢 NOVO CRUZAMENTO DE ALTA: BUY signal generated for {symbol}")
                        qty = risk_manager.calculate_position_size(settings.PAPER_TRADING_BALANCE, current_price) / current_price
                        sl, tp = risk_manager.calculate_sl_tp(current_price, "buy")
                        executor.execute_order(symbol, "buy", qty, current_price, sl, tp)

                elif previous_signal != -1 and current_signal == -1:
                    logger.info(f"🔴 NOVO CRUZAMENTO DE BAIXA: SELL signal generated for {symbol}")
                    db = SessionLocal()
                    try:
                        open_trades = db.query(Trade).filter(Trade.symbol == symbol, Trade.status == 'open', Trade.side == 'buy').all()
                        for trade in open_trades:
                            logger.info(f"Fechando posição de {symbol} por reversão de tendência.")
                            executor.close_order(trade.id, current_price)
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
