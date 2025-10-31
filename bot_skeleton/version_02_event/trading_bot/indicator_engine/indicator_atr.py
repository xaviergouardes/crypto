from collections import deque
from datetime import datetime
from typing import Deque, Optional
import numpy as np

from trading_bot.core.event_bus import EventBus
from trading_bot.core.events import CandleClose, CandleHistoryReady, IndicatorUpdated


class IndicatorATR:
    """
    Indicateur ATR (Average True Range) simple.
    Publie l'ATR à chaque bougie fermée.
    """

    def __init__(self, event_bus: EventBus, period: int = 14):
        self.event_bus = event_bus
        self.period = period

        # Historique des bougies
        self.candles: Deque = deque(maxlen=1000)
        self.symbol: Optional[str] = None
        self._initialized = False
        self.atr: Optional[float] = None

        # Souscriptions
        self.event_bus.subscribe(CandleHistoryReady, self.on_history_ready)
        self.event_bus.subscribe(CandleClose, self.on_candle_close)
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [IndicatorATR] période={self.period}")


    async def on_history_ready(self, event: CandleHistoryReady):
        """Initialise les bougies à partir de l'historique."""
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [IndicatorATR] Initialisation ...")

        if not event.candles:
            return

        self.symbol = event.symbol.upper()
        for candle in event.candles:
            self.candles.append(candle)

        self._initialized = True
        await self._compute_and_publish(event.candles[-1].end_time)
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [IndicatorATR] Initialisation Terminée {self.atr}")


    async def on_candle_close(self, event: CandleClose):
        """Ajoute la bougie et publie l'ATR."""
        if not self._initialized or event.symbol.upper() != self.symbol:
            return

        self.candles.append(event.candle)
        await self._compute_and_publish(event.candle.end_time)

    def _compute_atr_value(self):
        """Calcule l'ATR sur la période définie."""
        if len(self.candles) < self.period + 1:
            return None

        highs = np.array([c.high for c in list(self.candles)[-self.period-1:]])
        lows = np.array([c.low for c in list(self.candles)[-self.period-1:]])
        closes = np.array([c.close for c in list(self.candles)[-self.period-1:]])

        tr = np.maximum(highs[1:] - lows[1:], np.maximum(
            np.abs(highs[1:] - closes[:-1]),
            np.abs(lows[1:] - closes[:-1])
        ))

        return np.mean(tr)

    async def _compute_and_publish(self, timestamp: datetime):
        self.atr = self._compute_atr_value()
        if self.atr is None:
            return

        # Publication
        await self.event_bus.publish(
            IndicatorUpdated(
                symbol=self.symbol,
                timestamp=timestamp,
                values={
                    "type": self.__class__.__name__,
                    "atr": self.atr, 
                    "period": self.period
                }
            )
        )

    async def run(self):
        """Mode événementiel."""
        pass
