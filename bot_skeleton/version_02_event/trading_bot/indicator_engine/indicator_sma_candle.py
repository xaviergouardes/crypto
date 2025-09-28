from collections import deque
from typing import Deque, Optional
from datetime import datetime

from trading_bot.core.event_bus import EventBus
from trading_bot.core.events import CandleClose, CandleHistoryReady, IndicatorUpdated

class IndicatorSmaCandle:
    """
    Calcule une moyenne mobile simple (SMA) à partir des bougies clôturées.
    
    Peut s'initialiser avec un historique et continue ensuite en écoutant CandleClose.
    """

    def __init__(self, event_bus: EventBus, period: int = 20):
        self.event_bus = event_bus
        self.period = period
        self.candles: Deque[float] = deque(maxlen=period)  # stocke les clôtures récentes
        self._initialized = False
        self.symbol: Optional[str] = None

        # Souscription aux événements
        self.event_bus.subscribe(CandleClose, self.on_candle_close)
        self.event_bus.subscribe(CandleHistoryReady, self.on_history_ready)

    async def on_history_ready(self, event: CandleHistoryReady):
        """Initialisation du buffer à partir de l'historique reçu."""
        if not event.candles:
            return

        self.symbol = event.symbol.upper()
        for candle in event.candles[-self.period:]:
            self.candles.append(candle.close)

        self._initialized = True

        # Calcul initial de la SMA si assez de données
        if len(self.candles) == self.period:
            sma_value = sum(self.candles) / self.period
            await self.event_bus.publish(IndicatorUpdated(
                symbol=self.symbol,
                timestamp=event.candles[-1].end_time,
                values={
                    "sma_candle": sma_value,
                    "sma_candle_period": self.period
                }
            ))
            # print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [IndicatorSmaCandle] Initial SMA{self.period} ({self.symbol}) = {sma_value:.4f} @ {event.candles[-1].end_time}")

    async def on_candle_close(self, event: CandleClose) -> None:
        """Mise à jour de la SMA à chaque clôture de bougie."""
        # Vérifier que la classe est initialisée et que le symbole correspond
        if not self._initialized or event.symbol.upper() != self.symbol:
            return

        close_price = event.candle.close
        self.candles.append(close_price)

        # Calcul de la SMA si assez de données
        if len(self.candles) < self.period:
            return

        sma_value = sum(self.candles) / self.period

        await self.event_bus.publish(IndicatorUpdated(
            symbol=self.symbol,
            timestamp=event.candle.end_time,
            values={
                "sma_candle": sma_value,
                "sma_candle_period": self.period
            }
        ))

        # print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [IndicatorSmaCandle] 📈 SMA{self.period} ({self.symbol}) = {sma_value:.4f} @ {event.candle.end_time}")

    async def run(self):
        # Tout est événementiel
        pass
