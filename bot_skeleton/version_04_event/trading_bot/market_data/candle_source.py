# trading_bot/data_market/candle_source.py
from abc import ABC, abstractmethod
import pandas as pd

from trading_bot.core.event_bus import EventBus

class CandleSource(ABC):

    @abstractmethod
    def warmup(self, event_bus: EventBus):
        """Récupérer les bougie de warmup et génére un event pour les diffuser"""
        pass

    @abstractmethod
    async def stream(self, event_bus: EventBus):
        """ récupérer la bougie courante terminée et la diffuse via un event"""
        pass
