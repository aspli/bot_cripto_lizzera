import pandas as pd
import pandas_ta as ta
from app.strategies.base import BaseStrategy

class TrendFollowingStrategy(BaseStrategy):
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        if len(df) < 200:
            df['signal'] = 0
            return df
            
        # 1. Cálculo dos Indicadores de Preço
        df['EMA_20'] = ta.ema(df['close'], length=20)
        df['EMA_50'] = ta.ema(df['close'], length=50)
        df['EMA_200'] = ta.ema(df['close'], length=200)
        df['RSI'] = ta.rsi(df['close'], length=14)
        
        # 2. NOVO: Filtro de Volume (Média Móvel Simples de 20 períodos do Volume)
        df['SMA_Volume'] = ta.sma(df['volume'], length=20)
        
        # Inicializa a coluna de sinal
        df['signal'] = 0
        
        # 3. Condição de Volume: O volume da vela atual deve ser pelo menos 20% maior que a média
        volume_condition = df['volume'] > (df['SMA_Volume'] * 1.2)
        
        # 4. Condições Base
        buy_condition_base = (df['EMA_20'] > df['EMA_50']) & (df['RSI'] > 55) & (df['close'] > df['EMA_200']) & volume_condition
        sell_condition_base = (df['EMA_20'] < df['EMA_50']) | (df['RSI'] < 45)
        
        # 5. NOVO: Gatilho de Transição (Edge Trigger)
        # Retorna True apenas se a condição atual for True E a da vela anterior for False.
        # Isso impede que o bot emita múltiplos sinais "1" seguidos durante uma tendência.
        buy_trigger = buy_condition_base & (~buy_condition_base.shift(1).fillna(False))
        sell_trigger = sell_condition_base & (~sell_condition_base.shift(1).fillna(False))
        
        # 6. Aplicação dos Sinais
        df.loc[buy_trigger, 'signal'] = 1
        df.loc[sell_trigger, 'signal'] = -1
        
        return df