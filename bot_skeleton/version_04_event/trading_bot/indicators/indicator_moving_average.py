from collections import deque
from typing import Deque, Optional
from datetime import datetime
import numpy as np

from trading_bot.core.logger import Logger
from trading_bot.core.event_bus import EventBus
from trading_bot.core.events import CandleClose, CandleHistoryReady, IndicatorUpdated


class IndicatorMovingAverage:
    _logger = Logger.get("IndicatorMovingAverage")
    """
    Calcule une moyenne mobile (SMA ou EMA) à partir des bougies clôturées.

    Paramètres :
        - event_bus : EventBus pour recevoir les événements Candle
        - period : période de la moyenne
        - mode : "SMA" ou "EMA"
    """

    def __init__(self, event_bus: EventBus, period: int = 20, mode: str = "EMA"):
        if mode not in ("SMA", "EMA"):
            raise ValueError(f"Mode inconnu : {mode}. Choisir 'SMA' ou 'EMA'")

        self.event_bus = event_bus
        self.period = period
        self.mode = mode
        self.candles: Deque[float] = deque(maxlen=period)
        self.symbol: Optional[str] = None
        self._initialized = False
        self.current_value: Optional[float] = None
        self._sum: float = 0.0  # cumul pour SMA

        # Multiplier pour EMA
        self.multiplier = 2 / (period + 1)

        # Souscription aux événements
        self.event_bus.subscribe(CandleClose, self.on_candle_close)
        self.event_bus.subscribe(CandleHistoryReady, self.on_history_ready)
        self._logger.info(f"mode={self.mode} period={self.period}")

    # ------------------- Historique -------------------
    async def on_history_ready(self, event: CandleHistoryReady):
        self._logger.info("Initialisation ...")

        if not event.candles:
            return

        self.symbol = event.symbol.upper()
        candles_slice = event.candles[-self.period:]
        if not candles_slice:
            self._logger.warning(f"Pas de bougies disponibles pour {self.symbol}")
            return

        first_candle = candles_slice[0]
        last_candle = candles_slice[-1]
        # self._logger.debug(f"==> EMA period={self.period} Première bougie: {first_candle.start_time} / close={first_candle.close}")
        # self._logger.debug(f"==> EMA period={self.period} Dernière bougie: {last_candle.start_time} / close={last_candle.close}")

        closes = np.array([c.close for c in candles_slice], dtype=np.float64)
        self.candles = deque(closes, maxlen=self.period)

        if len(closes) < self.period:
            self._logger.warning(f"Pas assez de données ({len(closes)}/{self.period})")
            return

        if self.mode == "SMA":
            self.current_value = float(closes.mean())
            self._sum = float(closes.sum())
        elif self.mode == "EMA":
            alpha = self.multiplier
            weights = (1 - alpha) ** np.arange(len(closes) - 1, -1, -1)
            weights /= weights.sum()
            self.current_value = float(np.dot(closes, weights))

        self._initialized = True
        await self._publish(last_candle.end_time)

        # self._logger.debug("  Bougies utilisées pour le calcul initial de {self.mode}:")
        # for c in candles_slice:
        #     self._logger.debug(f"    {c}")

        self._logger.info("Initialisation Terminée"
              f"{last_candle} "
              f"{self.mode}({self.period}) = {self.current_value:.5f}"
              )
        

    # ------------------- Temps réel -------------------
    async def on_candle_close(self, event: CandleClose):
        """Met à jour la moyenne mobile à chaque clôture de bougie."""

        if not self._initialized or event.symbol.upper() != self.symbol.upper():
            return

        close_price = event.candle.close

        if self.mode == "SMA":
            if len(self.candles) == self.period:
                self._sum -= self.candles[0]
            self.candles.append(close_price)
            self._sum += close_price
            if len(self.candles) < self.period:
                return
            self.current_value = self._sum / self.period
            self._logger.debug(f"SMA mise à jour = {self.current_value:.5f}")

        elif self.mode == "EMA":
            if self.current_value is None and len(self.candles) < self.period:
                self.candles.append(close_price)
                if len(self.candles) == self.period:
                    self.current_value = sum(self.candles) / self.period
                    self._logger.debug(f"EMA initialisée = {self.current_value:.5f}")
            else:
                old_value = self.current_value
                self.current_value = (close_price - self.current_value) * self.multiplier + self.current_value
                # self._logger.debug(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  EMA({self.period})"
                #       f" mise à jour {old_value:.5f} → {self.current_value:.5f}"              
                #       f"{event.candle} "
                #       )

        if self.current_value is not None:
            await self._publish(event.candle.end_time)

    # ------------------- Publication -------------------
    async def _publish(self, timestamp: datetime):
        await self.event_bus.publish(
            IndicatorUpdated(
                symbol=self.symbol,
                timestamp=timestamp,
                values={
                    "type": self.__class__.__name__,
                    f"{self.mode.lower()}_candle": self.current_value,
                    f"{self.mode.lower()}_candle_period": self.period,
                }
            )
        )

