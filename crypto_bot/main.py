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
    """Verifica se o preço atual cruzou o Stop Loss ou Take Profit das ordens abertas."""
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
    """Sobe o Stop Loss usando o ATR se a posição for lucrativa (Trailing Stop)."""
    db = SessionLocal()
    try:
        open_trades = db.query(Trade).filter(Trade.symbol == symbol, Trade.status == 'open').all()
        for trade in open_trades:
            if trade.side == 'buy':
                # Distância do Stop: Preço Atual - (2x a volatilidade do ATR)
                novo_sl_potencial = current_price - (current_atr * 2)
                
                # Regra de Ouro: O stop só pode SUBIR
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
    notifier.send_message("🤖 Crypto Bot de Alta Performance iniciado.")

    while True:
        try:
            logger.info("Sincronizando dados com a Exchange...")
            collector.update_database()
            
            for symbol in settings.SYMBOLS:
                # Buscamos as últimas 250 velas do timeframe configurado
                df = collector.fetch_ohlcv(symbol, '1h', limit=250)
                if df.empty:
                    continue
                
                df_signals = strategy.generate_signals(df)
                
                # Extração de Preços e Volatilidade (Convertidos para float nativo para evitar erro do Numpy)
                current_price = float(df_signals.iloc[-1]['close']) 
                current_low = float(df_signals.iloc[-1]['low'])
                current_high = float(df_signals.iloc[-1]['high'])
                
                # Proteção caso o ATR retorne NaN nas primeiras velas
                current_atr = float(df_signals.iloc[-1]['ATR']) if not df_signals['ATR'].isna().iloc[-1] else 0.0
                
                # Extração dos Sinais da última e penúltima velas FECHADAS (Evita Repainting)
                current_signal = int(df_signals.iloc[-2]['signal'])
                previous_signal = int(df_signals.iloc[-3]['signal'])
                
                # ==========================================
                # 1. GERENCIAMENTO DE ORDENS PENDENTES (LIMIT)
                # ==========================================
                # Verifica se o preço atingiu alguma Limit Order (Ex: Grid Trading)
                if hasattr(executor, 'check_pending_orders'):
                    executor.check_pending_orders(current_low, current_high)
                
                # ==========================================
                # 2. GERENCIAMENTO DE RISCO E PROTEÇÃO (MARKET)
                # ==========================================
                check_open_trades_sl_tp(executor, current_price, symbol)
                if current_atr > 0:
                    manage_trailing_stops(executor, current_price, current_atr, symbol)
                
                # ==========================================
                # 3. AVALIAÇÃO DE NOVAS ENTRADAS (TRANSIÇÃO)
                # ==========================================
                # Só entra na OP se o sinal virou 1 AGORA (Edge Trigger)
                if previous_signal != 1 and current_signal == 1:
                    if risk_manager.can_open_trade(symbol):
                        logger.info(f"🟢 GATILHO DE COMPRA: Sinal confirmado para {symbol}")
                        
                        qty = float(risk_manager.calculate_position_size(settings.PAPER_TRADING_BALANCE, current_price) / current_price)
                        sl, tp = risk_manager.calculate_sl_tp(current_price, "buy")
                        
                        executor.execute_order(symbol, "buy", qty, current_price, sl, tp)
                
                # Só sai da OP se o sinal virou -1 AGORA
                elif previous_signal != -1 and current_signal == -1:
                    db = SessionLocal()
                    try:
                        open_trades = db.query(Trade).filter(Trade.symbol == symbol, Trade.status == 'open', Trade.side == 'buy').all()
                        for trade in open_trades:
                            logger.info(f"🔴 GATILHO DE VENDA: Fechando posição de {symbol} por reversão de tendência.")
                            executor.close_order(trade.id, current_price)
                    finally:
                        db.close()
            
            # Aguarda o próximo ciclo
            logger.info("Ciclo concluído. Dormindo por 60 segundos...")
            time.sleep(60)
            
        except KeyboardInterrupt:
            logger.info("Bot stopped by user.")
            notifier.send_message("🛑 Crypto Bot parado manualmente.")
            break
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()