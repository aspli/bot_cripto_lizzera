import pandas as pd
import pandas_ta as ta
from app.strategies.base import BaseStrategy

class TrendFollowingStrategy(BaseStrategy):

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        if len(df) < 200:
            df['signal'] = 0
            return df

        # Calculate indicators
        df['EMA_20'] = ta.ema(df['close'], length=20)
        df['EMA_50'] = ta.ema(df['close'], length=50)
        df['EMA_200'] = ta.ema(df['close'], length=200)
        df['RSI'] = ta.rsi(df['close'], length=14)

        # Initialize signal column
        df['signal'] = 0

        # We need to shift indicators by 1 if we are using them to trade on the current open,
        # or we just compute conditions for the current closed candle to trade on the next open.
        # For simplicity, we calculate the signal based on current row's completed data.

        # Buy condition: EMA20 > EMA50 and RSI > 55 and Close > EMA200 (trend filter)
        buy_condition = (df['EMA_20'] > df['EMA_50']) & (df['RSI'] > 55) & (df['close'] > df['EMA_200'])

        # Sell condition: EMA20 < EMA50 or RSI < 45
        sell_condition = (df['EMA_20'] < df['EMA_50']) | (df['RSI'] < 45)

        df.loc[buy_condition, 'signal'] = 1
        df.loc[sell_condition, 'signal'] = -1

        return df
