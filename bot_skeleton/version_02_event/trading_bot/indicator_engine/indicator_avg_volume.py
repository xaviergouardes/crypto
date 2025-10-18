from collections import deque
from datetime import datetime
from typing import Deque, Optional
import numpy as np

from trading_bot.core.event_bus import EventBus
from trading_bot.core.events import CandleClose, CandleHistoryReady, IndicatorUpdated


class IndicatorAvgVolume:
    """
    Indicateur de volume moyen simple.
    Publie le volume moyen sur une période donnée à chaque bougie fermée.
    """

    def __init__(self, event_bus: EventBus, period: int = 14):
        self.event_bus = event_bus
        self.period = period

        # Historique des bougies
        self.candles: Deque = deque(maxlen=1000)
        self.symbol: Optional[str] = None
        self._initialized = False
        self.avg_volume: Optional[float] = None

        # Souscriptions aux événements
        self.event_bus.subscribe(CandleHistoryReady, self.on_history_ready)
        self.event_bus.subscribe(CandleClose, self.on_candle_close)
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [IndicatorAvgVolume] période={self.period}")

    async def on_history_ready(self, event: CandleHistoryReady):
        """Initialise les bougies à partir de l'historique."""
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [IndicatorAvgVolume] Initialisation ...")

        if not event.candles:
            return

        self.symbol = event.symbol.upper()
        for candle in event.candles:
            self.candles.append(candle)

        self._initialized = True
        await self._compute_and_publish(event.candles[-1].end_time)
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [IndicatIndicatorAvgVolumeorATR] Initialisation Terminée {self.avg_volume}")


    async def on_candle_close(self, event: CandleClose):
        """Ajoute la bougie et publie le volume moyen."""
        if not self._initialized or event.symbol.upper() != self.symbol:
            return

        self.candles.append(event.candle)
        await self._compute_and_publish(event.candle.end_time)

    def _compute_avg_volume(self):
        """Calcule le volume moyen sur la période."""
        if len(self.candles) < self.period:
            return None

        volumes = np.array([c.volume for c in list(self.candles)[-self.period:]])
        return np.mean(volumes)

    async def _compute_and_publish(self, timestamp: datetime):
        self.avg_volume = self._compute_avg_volume()
        if self.avg_volume is None:
            return

        # Publication
        await self.event_bus.publish(
            IndicatorUpdated(
                symbol=self.symbol,
                timestamp=timestamp,
                values={"avg_volume": self.avg_volume, "period": self.period}
            )
        )

    async def run(self):
        """Mode événementiel."""
        pass
