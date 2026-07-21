import time
import logging
from app.config.settings import settings
from app.data.models import init_db, SessionLocal, Trade
from app.data.collector import DataCollector
from app.strategies.trend_following import TrendFollowingStrategy
from app.risk_management.manager import RiskManager
from app.execution.executor import Executor
from app.notifications.telegram import TelegramNotifier

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_open_trades_sl_tp(executor, current_price, symbol):
    """Verifica se o preço atual cruzou o Stop Loss ou Take Profit."""
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
    finally:
        db.close()

def manage_trailing_stops(executor, current_price, current_atr, symbol):
    """Sobe o Stop Loss usando o ATR se a posição for lucrativa."""
    db = SessionLocal()
    try:
        open_trades = db.query(Trade).filter(Trade.symbol == symbol, Trade.status == 'open').all()
        for trade in open_trades:
            if trade.side == 'buy':
                # Distância padrão: Preço Atual - (2x a volatilidade do ATR)
                novo_sl_potencial = current_price - (current_atr * 2)
                
                # Regra de Ouro do TS: O stop só pode SUBIR
                if trade.stop_loss and novo_sl_potencial > trade.stop_loss:
                    executor.update_stop_loss(trade.id, novo_sl_potencial)
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
    notifier.send_message("🤖 Crypto Bot com ATR Trailing Stop iniciado.")

    while True:
        try:
            collector.update_database()
            
            for symbol in settings.SYMBOLS:
                df = collector.fetch_ohlcv(symbol, '1h', limit=250)
                if df.empty:
                    continue
                
                df_signals = strategy.generate_signals(df)
                
                # Preços e Sinais
                current_signal = df_signals.iloc[-2]['signal']
                previous_signal = df_signals.iloc[-3]['signal']
                current_price = df_signals.iloc[-1]['close'] 
                current_atr = df_signals.iloc[-1]['ATR'] # Pegamos a volatilidade do momento
                
                # 1. VERIFICAR SL/TP E ATUALIZAR TRAILING STOP
                check_open_trades_sl_tp(executor, current_price, symbol)
                manage_trailing_stops(executor, current_price, current_atr, symbol)
                
                # 2. AVALIAR NOVOS SINAIS (Apenas na transição)
                if previous_signal != 1 and current_signal == 1:
                    if risk_manager.can_open_trade(symbol):
                        logger.info(f"🟢 BUY signal para {symbol}")
                        qty = risk_manager.calculate_position_size(settings.PAPER_TRADING_BALANCE, current_price) / current_price
                        
                        # O Stop inicial também pode ser definido pelo ATR aqui, ou manter o fixo do RiskManager
                        sl, tp = risk_manager.calculate_sl_tp(current_price, "buy")
                        executor.execute_order(symbol, "buy", qty, current_price, sl, tp)
                
                elif previous_signal != -1 and current_signal == -1:
                    db = SessionLocal()
                    try:
                        open_trades = db.query(Trade).filter(Trade.symbol == symbol, Trade.status == 'open', Trade.side == 'buy').all()
                        for trade in open_trades:
                            logger.info(f"Fechando posição de {symbol} por reversão de tendência.")
                            executor.close_order(trade.id, current_price)
                    finally:
                        db.close()
            
            # Correção de eficiência: aguardar até o próximo ciclo
            time.sleep(60)
            
        except KeyboardInterrupt:
            logger.info("Bot stopped by user.")
            break
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
