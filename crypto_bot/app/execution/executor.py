import logging
from app.config.settings import settings
from app.data.models import SessionLocal, Trade
import datetime

logger = logging.getLogger(__name__)

class Executor:
    def __init__(self, notifier=None):
        self.mode = settings.TRADING_MODE
        self.paper_balance = settings.PAPER_TRADING_BALANCE
        self.notifier = notifier

    def execute_order(self, symbol: str, side: str, quantity: float, price: float, sl: float = None, tp: float = None):
        quantity = float(quantity)
        price = float(price)
        if sl is not None:
            sl = float(sl)
        if tp is not None:
            tp = float(tp)
            
        if self.mode == "paper":
            self._paper_trade(symbol, side, quantity, price, sl, tp)
        else:
            self._live_trade(symbol, side, quantity, price, sl, tp)

    def _paper_trade(self, symbol: str, side: str, quantity: float, price: float, sl: float = None, tp: float = None):
        db = SessionLocal()
        try:
            logger.info(f"PAPER TRADE: {side} {quantity} {symbol} @ {price} | SL: {sl} | TP: {tp}")
            
            trade = Trade(
                symbol=symbol,
                side=side,
                entry_price=price,
                quantity=quantity,
                status="open",
                stop_loss=sl,       
                take_profit=tp      
            )
            db.add(trade)
            db.commit()
            
            if self.notifier:
                self.notifier.send_message(f"🚨 PAPER TRADE ENTRY: {side} {symbol}\nPreço: {price}\nSL: {sl}\nTP: {tp}")
                
        except Exception as e:
            logger.error(f"Error in paper trade execution: {e}")
            db.rollback()
        finally:
            db.close()
            
    def update_stop_loss(self, trade_id: int, new_sl: float):
        new_sl = float(new_sl)
        db = SessionLocal()
        try:
            trade = db.query(Trade).filter(Trade.id == trade_id).first()
            if not trade:
                return
            
            trade.stop_loss = new_sl
            db.commit()
            logger.info(f"🛡️ Trailing Stop Atualizado: {trade.symbol} | Novo SL: {new_sl:.2f}")
            
            # Opcional: Enviar mensagem no Telegram a cada ajuste (pode gerar muito spam, cuidado)
            # if self.notifier:
            #     self.notifier.send_message(f"🛡️ Trailing Stop ajustado para {trade.symbol} em {new_sl:.2f}")
                
        except Exception as e:
            logger.error(f"Erro ao atualizar Stop Loss: {e}")
            db.rollback()
        finally:
            db.close()

    def close_order(self, trade_id: int, exit_price: float):
        db = SessionLocal()
        try:
            trade = db.query(Trade).filter(Trade.id == trade_id).first()
            if not trade:
                return

            trade.exit_price = exit_price
            trade.exit_time = datetime.datetime.utcnow()
            trade.status = "closed"

            if trade.side == "buy":
                trade.pnl = (exit_price - trade.entry_price) * trade.quantity
            else:
                trade.pnl = (trade.entry_price - exit_price) * trade.quantity

            db.commit()
            logger.info(f"CLOSED TRADE: {trade.symbol} PNL: {trade.pnl}")

            if self.notifier:
                self.notifier.send_message(f"✅ TRADE CLOSED: {trade.symbol} | PNL: {trade.pnl:.2f}")

        except Exception as e:
            logger.error(f"Error closing order: {e}")
            db.rollback()
        finally:
            db.close()

    def _live_trade(self, symbol: str, side: str, quantity: float, price: float):
        # Placeholder for live execution via CCXT
        logger.warning("Live trading is not fully implemented yet.")
        pass

    def place_limit_order(self, symbol: str, side: str, quantity: float, price: float, sl: float = None, tp: float = None):
        """Envia uma ordem limite para o Livro de Ofertas (Status inicial: pending)."""
        quantity = float(quantity)
        price = float(price)
        if sl: sl = float(sl)
        if tp: tp = float(tp)
        
        db = SessionLocal()
        try:
            logger.info(f"⏳ PENDING LIMIT ORDER: {side} {quantity} {symbol} @ {price}")
            
            # No modo Live, aqui você chamaria: self.exchange.create_limit_order(...)
            # e salvaria o ID retornado em exchange_order_id.
            
            trade = Trade(
                symbol=symbol,
                side=side,
                order_type="limit",
                entry_price=price,
                quantity=quantity,
                status="pending", # Nasce pendente
                stop_loss=sl,
                take_profit=tp
            )
            db.add(trade)
            db.commit()
            
        except Exception as e:
            logger.error(f"Erro ao criar ordem limite: {e}")
            db.rollback()
        finally:
            db.close()

    def check_pending_orders(self, current_low: float, current_high: float):
        """
        Verifica se o preço atual cruzou as ordens pendentes.
        No Live, isso seria feito consultando a API: self.exchange.fetch_order(id)
        """
        db = SessionLocal()
        try:
            pending_trades = db.query(Trade).filter(Trade.status == 'pending').all()
            for trade in pending_trades:
                filled = False
                
                # Se for compra limite, o preço tem que cair até o alvo ou mais baixo
                if trade.side == 'buy' and current_low <= trade.entry_price:
                    filled = True
                
                # Se for venda limite, o preço tem que subir até o alvo ou mais alto
                elif trade.side == 'sell' and current_high >= trade.entry_price:
                    filled = True
                    
                if filled:
                    trade.status = "open"
                    trade.entry_time = datetime.datetime.utcnow()
                    logger.info(f"✅ LIMIT ORDER FILLED: {trade.side} {trade.symbol} @ {trade.entry_price}")
                    
                    if self.notifier:
                        self.notifier.send_message(f"✅ Ordem Limite Executada: {trade.side} {trade.symbol} a {trade.entry_price}")
            
            db.commit()
        finally:
            db.close()