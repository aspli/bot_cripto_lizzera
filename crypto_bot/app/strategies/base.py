from abc import ABC, abstractmethod
import pandas as pd

class BaseStrategy(ABC):

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculates indicators and generates signals.
        Expected to add a 'signal' column: 1 for buy, -1 for sell, 0 for hold.
        """
        pass
