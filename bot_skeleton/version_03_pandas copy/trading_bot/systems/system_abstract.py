# trading_bot/data_market/candle_source.py
from abc import ABC, abstractmethod
import pandas as pd

class System(ABC):

    @abstractmethod
    def run(self, df: pd.DataFrame) -> pd.DataFrame:
        pass

