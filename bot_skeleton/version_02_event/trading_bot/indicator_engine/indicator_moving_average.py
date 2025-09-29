from collections import deque
from typing import Deque, Optional
from datetime import datetime

from trading_bot.core.event_bus import EventBus
from trading_bot.core.events import CandleClose, CandleHistoryReady, IndicatorUpdated


class IndicatorMovingAverage:
    """
    Calcule une moyenne mobile (SMA ou EMA) à partir des bougies clôturées.

    Paramètres :
        - event_bus : EventBus pour recevoir les événements Candle
        - period : période de la moyenne
        - mode : "SMA" ou "EMA"
    """

    def __init__(self, event_bus: EventBus, period: int = 20, mode: str = "SMA"):
        if mode not in ("SMA", "EMA"):
            raise ValueError(f"Mode inconnu : {mode}. Choisir 'SMA' ou 'EMA'")

        self.event_bus = event_bus
        self.period = period
        self.mode = mode
        self.candles: Deque[float] = deque(maxlen=period)
        self.symbol: Optional[str] = None
        self._initialized = False
        self.current_value: Optional[float] = None

        # Multiplier pour EMA
        self.multiplier = 2 / (period + 1)

        # Souscription aux événements
        self.event_bus.subscribe(CandleClose, self.on_candle_close)
        self.event_bus.subscribe(CandleHistoryReady, self.on_history_ready)
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [IndicatorMovingAverage] mode={self.mode} period={self.period}")
 

    # -----------------------------------------------------
    # Historique
    # -----------------------------------------------------
    async def on_history_ready(self, event: CandleHistoryReady):
        """Initialise le buffer à partir de l'historique reçu."""
        if not event.candles:
            return

        self.symbol = event.symbol.upper()
        for candle in event.candles[-self.period:]:
            self.candles.append(candle.close)

        self._initialized = True

        if len(self.candles) == self.period:
            # Calcul initial
            if self.mode == "SMA":
                self.current_value = sum(self.candles) / self.period
            elif self.mode == "EMA":
                self.current_value = sum(self.candles) / self.period  # première EMA = SMA
            await self._publish(event.candles[-1].end_time)

    # -----------------------------------------------------
    # Temps réel
    # -----------------------------------------------------
    async def on_candle_close(self, event: CandleClose):
        """Met à jour la moyenne mobile à chaque clôture de bougie."""
        # print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [IndicatorMovingAverage] onCandleClose")
 
        if not self._initialized or event.symbol.upper() != self.symbol:
            return

        close_price = event.candle.close

        if self.mode == "SMA":
            self.candles.append(close_price)
            if len(self.candles) < self.period:
                return
            self.current_value = sum(self.candles) / self.period

        elif self.mode == "EMA":
            if self.current_value is None:
                # EMA non initialisée : attendre le buffer plein pour init SMA
                self.candles.append(close_price)
                if len(self.candles) == self.period:
                    self.current_value = sum(self.candles) / self.period
                    # print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [IndicatorMovingAverage] EMA = {self.current_value}")
            else:
                # EMA récursive
                self.current_value = (close_price - self.current_value) * self.multiplier + self.current_value
                # print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [IndicatorMovingAverage] Récursive EMA = {self.current_value}")

        if self.current_value is not None:
            await self._publish(event.candle.end_time)

    # -----------------------------------------------------
    # Publication
    # -----------------------------------------------------
    async def _publish(self, timestamp: datetime):
        """Publie l'événement IndicatorUpdated avec la valeur calculée."""
        # print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [IndicatorMovingAverage] Event Publich  {self.mode.lower()}_candle={self.current_value}")

        await self.event_bus.publish(
            IndicatorUpdated(
                symbol=self.symbol,
                timestamp=timestamp,
                values={
                    f"{self.mode.lower()}_candle": self.current_value,
                    f"{self.mode.lower()}_candle_period": self.period,
                }
            )
        )

    async def run(self):
        # Tout est événementiel
        pass
