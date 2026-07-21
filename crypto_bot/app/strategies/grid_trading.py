import pandas as pd
import numpy as np
import logging
from app.strategies.base import BaseStrategy

logger = logging.getLogger(__name__)

class GridStrategy(BaseStrategy):
    def __init__(self, lower_price: float, upper_price: float, num_grids: int):
        """
        Inicializa a malha de ordens.
        """
        self.lower_price = lower_price
        self.upper_price = upper_price
        self.num_grids = num_grids
        
        # Gera os níveis de preço da malha matemática
        self.grid_levels = np.linspace(self.lower_price, self.upper_price, self.num_grids + 1)
        
        # Dicionário para manter o "estado" da malha na memória
        # False = Não comprado | True = Comprado e aguardando venda
        self.grid_state = {round(level, 2): False for level in self.grid_levels}
        
        logger.info(f"🕸️ Malha Grid Criada: {self.num_grids} níveis entre {self.lower_price} e {self.upper_price}")

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        No Grid, não geramos sinais para o passado inteiro. 
        Avaliamos apenas se o preço de fechamento atual rompeu algum nível da malha.
        """
        # Inicializa a coluna neutra
        df['signal'] = 0 
        
        # Pega o preço de fechamento mais recente
        current_price = df.iloc[-1]['close']
        
        # Localiza em qual "andar" do grid o preço atual está
        # Retorna o índice do nível imediatamente inferior ao preço atual
        current_level_idx = np.searchsorted(self.grid_levels, current_price, side='right') - 1
        
        # Proteção para fora do range da malha
        if current_level_idx < 0 or current_level_idx >= len(self.grid_levels):
            return df
            
        current_level_price = round(self.grid_levels[current_level_idx], 2)
        next_level_price = round(self.grid_levels[current_level_idx + 1], 2) if current_level_idx + 1 < len(self.grid_levels) else None
        
        # LÓGICA DE COMPRA (Preço desceu, atingiu a linha inferior e ela ainda não foi comprada)
        if not self.grid_state[current_level_price]:
            self.grid_state[current_level_price] = True # Atualiza o estado
            df.loc[df.index[-1], 'signal'] = 1 # Dispara compra
            df.loc[df.index[-1], 'target_price'] = current_level_price
            logger.info(f"📉 Grid Nível {current_level_price} atingido. Sinal de COMPRA.")
            
        # LÓGICA DE VENDA (Preço subiu, atingiu a linha superior de um andar já comprado)
        elif next_level_price and self.grid_state[current_level_price]:
            # Limpa o andar atual para poder comprar de novo se o preço cair
            self.grid_state[current_level_price] = False 
            df.loc[df.index[-1], 'signal'] = -1 # Dispara venda
            df.loc[df.index[-1], 'target_price'] = next_level_price
            logger.info(f"📈 Grid Nível {next_level_price} atingido. Sinal de VENDA (Realização de Lucro).")
            
        return df