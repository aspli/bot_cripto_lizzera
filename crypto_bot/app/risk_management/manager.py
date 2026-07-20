import logging
from app.config.settings import settings
from app.data.models import SessionLocal, Trade

logger = logging.getLogger(__name__)

class RiskManager:

    def __init__(self):
        self.max_risk_per_trade = settings.MAX_RISK_PER_TRADE
        self.max_open_trades = settings.MAX_OPEN_TRADES
        self.default_stop_loss_pct = settings.DEFAULT_STOP_LOSS_PCT
        self.default_take_profit_pct = settings.DEFAULT_TAKE_PROFIT_PCT

    def can_open_trade(self, symbol: str) -> bool:
        db = SessionLocal()
        try:
            # Check max open trades
            open_trades = db.query(Trade).filter(Trade.status == 'open').count()
            if open_trades >= self.max_open_trades:
                logger.info("Maximum open trades reached.")
                return False

            # Check if we already have an open trade for this symbol
            existing_trade = db.query(Trade).filter(
                Trade.symbol == symbol,
                Trade.status == 'open'
            ).first()

            if existing_trade:
                logger.info(f"Already have an open trade for {symbol}.")
                return False

            return True
        finally:
            db.close()

    def calculate_position_size(self, current_balance: float, current_price: float) -> float:
        """
        Calculate position size based on risking 1% of the total capital.
        Assuming a fixed Stop Loss %.
        """
        risk_amount = current_balance * self.max_risk_per_trade
        # The amount we lose if SL hits is position_size * current_price * SL_pct
        # So position_size = risk_amount / (current_price * SL_pct)

        position_size = risk_amount / (current_price * self.default_stop_loss_pct)
        return position_size

    def calculate_sl_tp(self, entry_price: float, side: str) -> tuple[float, float]:
        if side == "buy":
            sl = entry_price * (1 - self.default_stop_loss_pct)
            tp = entry_price * (1 + self.default_take_profit_pct)
        else:
            sl = entry_price * (1 + self.default_stop_loss_pct)
            tp = entry_price * (1 - self.default_take_profit_pct)
        return sl, tp
