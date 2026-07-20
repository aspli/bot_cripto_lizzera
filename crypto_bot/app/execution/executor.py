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

    def execute_order(self, symbol: str, side: str, quantity: float, price: float):
        if self.mode == "paper":
            self._paper_trade(symbol, side, quantity, price)
        else:
            self._live_trade(symbol, side, quantity, price)

    def _paper_trade(self, symbol: str, side: str, quantity: float, price: float):
        db = SessionLocal()
        try:
            logger.info(f"PAPER TRADE: {side} {quantity} {symbol} @ {price}")

            # Record the trade
            trade = Trade(
                symbol=symbol,
                side=side,
                entry_price=price,
                quantity=quantity,
                status="open"
            )
            db.add(trade)
            db.commit()

            if self.notifier:
                self.notifier.send_message(f"🚨 PAPER TRADE ENTRY: {side} {symbol} @ {price}")

        except Exception as e:
            logger.error(f"Error in paper trade execution: {e}")
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
