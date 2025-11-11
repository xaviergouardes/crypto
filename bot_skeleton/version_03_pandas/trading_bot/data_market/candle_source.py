# trading_bot/data_market/candle_source.py
from abc import ABC, abstractmethod
import pandas as pd

class CandleSource(ABC):
    @abstractmethod
    def get_initial_data(self) -> pd.DataFrame:
        """Retourne un DataFrame initial (historique minimal nécessaire)."""
        pass

    @abstractmethod
    async def stream_candles(self, on_new_candle):
        """Lance le flux et appelle `on_new_candle(candle_dict)` à chaque bougie clôturée."""
        pass
